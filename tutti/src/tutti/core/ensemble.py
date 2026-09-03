"""Route live strikes to bots, under the same physics the planner enforces.

Scored playback knows the whole future, so plan_score can nudge, reassign and
report before anything moves. A live source knows nothing until a hand is
already coming down. What must not change between those two worlds is the
physics: which bot accepts which note, how soon a voice can fire again, and
what happens when the answer is "it cannot". The Ensemble is the planner's
inner loop re-run one strike at a time, on the same BotState objects, so the
two paths cannot drift apart.

The other job it does is the one the old firmware never could: when a strike
is physically impossible, it says so, with a reason, instead of silently
eating it.
"""

from __future__ import annotations

import threading
import time
from collections import Counter, deque
from dataclasses import dataclass

from ..transports.base import Transport
from .plan import BotState, Instrument, ScheduledHit

DEFAULT_TOLERANCE_MS = 15.0


@dataclass(frozen=True)
class StrikeResult:
    """What became of one requested strike."""

    ok: bool
    bot_id: str = ""
    voice: int = -1
    note: int = 0
    play_at_s: float = 0.0
    nudge_ms: float = 0.0
    reason: str = ""      # set when ok is False, or "muted"
    detail: str = ""


class Ensemble:
    """The bots that are on stage right now, and the one way to strike them."""

    def __init__(
        self,
        instruments: dict[str, Instrument],
        transport: Transport,
        tolerance_ms: float = DEFAULT_TOLERANCE_MS,
        clock=None,
    ) -> None:
        self._instruments = dict(instruments)
        self._transport = transport
        self._tolerance_s = tolerance_ms / 1000.0
        self._states = {bot_id: BotState(inst) for bot_id, inst in instruments.items()}
        self._lock = threading.Lock()

        if clock is not None:
            self._clock = clock
        elif hasattr(type(transport), "now_s"):
            self._clock = lambda: transport.now_s
        else:
            origin = time.monotonic()
            self._clock = lambda: time.monotonic() - origin

        self.muted = False
        self.hits = 0
        self.suppressed = 0
        self.drop_reasons: Counter[str] = Counter()
        self.recent: deque[StrikeResult] = deque(maxlen=64)

    @property
    def instruments(self) -> dict[str, Instrument]:
        return dict(self._instruments)

    @property
    def dropped(self) -> int:
        return sum(self.drop_reasons.values())

    def now_s(self) -> float:
        return self._clock()

    def max_live_lead_s(self) -> float:
        """How early a strike must be requested to be honest for every bot.

        A live source planning on a beat grid asks this once and runs that
        far ahead of real time, so the first note of a beat is still
        physically reachable when it is handed over.
        """
        return max(
            (self._transport.live_lead_s(bot_id) for bot_id in self._instruments),
            default=0.0,
        )

    def strike(self, note: int, velocity: int = 100, source: str = "") -> StrikeResult:
        """Play one note as soon as physics allows, or say why it cannot.

        The walk over candidate bots is the same nudge-then-reassign-then-drop
        sequence plan_score runs, against a shared view of voice availability,
        so a bot saturated by one source is correctly unavailable to another.
        """
        return self._place(note, velocity, None, source)

    def strike_at(self, note: int, velocity: int, at_s: float, source: str = "") -> StrikeResult:
        """Schedule one note for a chosen instant, or say why it cannot land there.

        at_s is on the same clock as now_s(). The hit is handed to the
        transport immediately — every transport holds early hits until they
        are due — and the same physics walk applies as for strike(); only the
        requested time differs. A target closer than a bot's live lead cannot
        be honoured honestly and is dropped as "too_late" rather than played
        audibly behind the grid.
        """
        return self._place(note, velocity, at_s, source)

    def _place(self, note: int, velocity: int, at_s: float | None, source: str) -> StrikeResult:
        with self._lock:
            if self.muted:
                self.suppressed += 1
                result = StrikeResult(ok=False, note=note, reason="muted")
                self.recent.append(result)
                return result

            now = self._clock()
            near_miss: tuple[str, str] | None = None
            accepted_anywhere = False
            first_choice = ""

            for bot_id, state in self._states.items():
                floor = now + self._transport.live_lead_s(bot_id)
                # target is the musical intent; requested is the earliest the
                # physics may consider, which can be later than asked for.
                target = floor if at_s is None else at_s
                requested = max(target, floor)
                slot = state.earliest(note, requested)
                if slot is None:
                    continue
                accepted_anywhere = True
                if not first_choice:
                    first_choice = bot_id
                voice, at = slot

                if at - target <= self._tolerance_s:
                    state.commit(voice, at)
                    hit = ScheduledHit(
                        part_id=0,
                        bot_id=bot_id,
                        voice=voice,
                        note=note,
                        velocity=velocity,
                        play_at_s=at,
                        requested_s=target,
                        first_choice_bot=first_choice,
                    )
                    self._transport.send([hit])
                    self.hits += 1
                    result = StrikeResult(
                        ok=True, bot_id=bot_id, voice=voice, note=note,
                        play_at_s=at, nudge_ms=(at - target) * 1000.0,
                    )
                    self.recent.append(result)
                    return result

                if near_miss is None:
                    if floor - target > self._tolerance_s:
                        near_miss = ("too_late",
                                     f"needed {(floor - target) * 1000.0:.1f}ms more lead")
                    else:
                        near_miss = state.blocking_reason(note, requested, at)

            if not accepted_anywhere:
                reason, detail = "note_not_accepted", f"no bot on stage plays note {note}"
            else:
                reason, detail = near_miss or ("cycle_not_ready", "")
            self.drop_reasons[reason] += 1
            result = StrikeResult(ok=False, note=note, reason=reason, detail=detail)
            self.recent.append(result)
            return result

    def command(self, name: str) -> None:
        """Apply a performance command from any source.

        STOP and ARM are the pair that matters live: a closed fist silences
        the kit without tearing the pipeline down, an open palm brings it back.
        Anything else is recorded so a status line can show it, and ignored,
        which is the honest behaviour until something implements it.
        """
        if name == "STOP":
            self.muted = True
        elif name == "ARM":
            self.muted = False

    def status(self) -> dict:
        return {
            "hits": self.hits,
            "dropped": self.dropped,
            "drop_reasons": dict(self.drop_reasons),
            "suppressed": self.suppressed,
            "muted": self.muted,
            "bots": sorted(self._instruments),
        }
