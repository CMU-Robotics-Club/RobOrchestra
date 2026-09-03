"""Decide when each bot actually strikes, given what it can physically do.

Every bot has a hard floor on how fast it can hit: a stick has to travel down,
come back up, and only then can it fire again. The legacy firmware discovers
this at play time and silently discards whatever it cannot manage. The comment
in snarebot_servo_midi.ino says as much:

    //I'd like to throw an error or print something or do something otherwise
    //weird; not sure if I can do that

So the planner does that work up front instead. It walks the score, assigns
each note to a real voice on a real bot, shifts notes slightly when that is
enough to make them fit, moves them to another bot when it is not, and records
a reason for every note it still cannot place.

The assignment is greedy in time order, not optimal. That is deliberate: it is
the same rule the firmware follows online, it runs in one pass, and when it
drops a note you can point at the note before it and see why.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .score import Score

# How far a note may be shifted before anyone would hear it move. Percussion
# tolerates a little; 15 ms is roughly the threshold for a single attack.
DEFAULT_TOLERANCE_MS = 15.0

POOLED = "pooled"   # any free voice can play any accepted note, e.g. 2 drum sticks
KEYED = "keyed"     # the note picks the voice, e.g. one solenoid per xylophone key


class PlanError(Exception):
    pass


@dataclass(frozen=True)
class ActuatorModel:
    """What one bot can physically do.

    Times are in milliseconds because that is how the firmware and the people
    tuning it think about them.
    """

    voices: int
    cycle_ms: float                 # per voice: down time plus recovery
    accepts: frozenset[int]
    voice_mode: str = POOLED
    spacing_ms: float = 0.0         # floor between any two hits on this bot
    mech_latency_ms: float = 0.0    # travel time, compensated bot-locally
    mech_jitter_ms: float = 0.0
    max_concurrent: int | None = None    # power limit for solenoid banks
    lowest_note: int = 0            # keyed mode: which note is voice 0
    velocity: bool = False
    sustain: bool = False

    def __post_init__(self):
        if self.voices < 1:
            raise PlanError("a bot needs at least one voice")
        if self.cycle_ms <= 0:
            raise PlanError("cycle_ms must be positive")
        if self.voice_mode not in (POOLED, KEYED):
            raise PlanError(f"unknown voice_mode {self.voice_mode!r}")

    @property
    def cycle_s(self) -> float:
        return self.cycle_ms / 1000.0

    @property
    def spacing_s(self) -> float:
        return self.spacing_ms / 1000.0

    @property
    def min_gap_ms(self) -> float:
        """Shortest sustainable gap between consecutive hits."""
        if self.voice_mode == KEYED:
            return self.cycle_ms      # per key; different keys are independent
        return max(self.cycle_ms / self.voices, self.spacing_ms)

    @property
    def max_rate_hz(self) -> float:
        return 1000.0 / self.min_gap_ms

    def voice_for(self, note: int) -> int | None:
        """Which voice must play this note, or None if any free voice will do."""
        if self.voice_mode != KEYED:
            return None
        index = note - self.lowest_note
        return index if 0 <= index < self.voices else None


@dataclass(frozen=True)
class Instrument:
    bot_id: str
    role: str
    model: ActuatorModel


@dataclass(frozen=True)
class ScheduledHit:
    part_id: int
    bot_id: str
    voice: int
    note: int
    velocity: int
    play_at_s: float
    requested_s: float
    first_choice_bot: str = ""

    @property
    def nudge_ms(self) -> float:
        return (self.play_at_s - self.requested_s) * 1000.0

    @property
    def reassigned(self) -> bool:
        return bool(self.first_choice_bot) and self.first_choice_bot != self.bot_id


@dataclass(frozen=True)
class Drop:
    part_id: int
    note: int
    requested_s: float
    reason: str
    detail: str = ""


@dataclass
class Plan:
    hits: list[ScheduledHit] = field(default_factory=list)
    drops: list[Drop] = field(default_factory=list)
    tempo_scale: float = 1.0

    @property
    def feasible(self) -> bool:
        return not self.drops

    @property
    def nudged(self) -> list[ScheduledHit]:
        return [h for h in self.hits if abs(h.nudge_ms) > 1e-6]

    @property
    def reassigned(self) -> list[ScheduledHit]:
        return [h for h in self.hits if h.reassigned]

    def for_part(self, part_id: int) -> list[ScheduledHit]:
        return [h for h in self.hits if h.part_id == part_id]

    def drops_for_part(self, part_id: int) -> list[Drop]:
        return [d for d in self.drops if d.part_id == part_id]


class BotState:
    """Tracks when each voice on one bot is next free.

    This is the online form of the constraint model: plan_score uses it to walk
    a whole score in advance, and the live Ensemble uses the same object to
    answer one strike at a time as a human plays. Keeping both on one class is
    deliberate, so the two paths can never disagree about what a bot can do.
    """

    def __init__(self, instrument: Instrument):
        self.instrument = instrument
        self.model = instrument.model
        self.free_at = [float("-inf")] * self.model.voices
        self.last_any = float("-inf")
        self.next_voice = 0     # round robin, only to even out wear

    def earliest(self, note: int, requested_s: float) -> tuple[int, float] | None:
        """Earliest time this bot can strike `note`, and which voice does it.

        Returns None when the note is not one this bot plays at all.
        """
        if note not in self.model.accepts:
            return None

        forced = self.model.voice_for(note)
        if forced is not None:
            candidates = [forced]
        elif self.model.voice_mode == KEYED:
            return None     # keyed bot, note maps to no key
        else:
            candidates = list(range(self.model.voices))

        best_voice, best_time = None, float("inf")
        for offset in range(len(candidates)):
            # Rotate the start point so equal-ready voices alternate.
            v = candidates[(self.next_voice + offset) % len(candidates)]
            ready = max(self.free_at[v] + self.model.cycle_s, requested_s)
            if self.model.spacing_s:
                ready = max(ready, self.last_any + self.model.spacing_s)
            if ready < best_time:
                best_voice, best_time = v, ready

        if best_voice is None:
            return None
        return best_voice, best_time

    def commit(self, voice: int, at_s: float) -> None:
        self.free_at[voice] = at_s
        self.last_any = at_s
        self.next_voice = (voice + 1) % self.model.voices

    def blocking_reason(self, note: int, requested_s: float, actual_s: float) -> tuple[str, str]:
        gap_ms = (requested_s - self.last_any) * 1000.0
        if self.model.spacing_s and requested_s < self.last_any + self.model.spacing_s:
            return ("global_spacing",
                    f"gap {gap_ms:.1f}ms < spacing {self.model.spacing_ms:.1f}ms")
        deficit_ms = (actual_s - requested_s) * 1000.0
        return ("cycle_not_ready",
                f"sustainable cycle/voice is {self.model.min_gap_ms:.1f}ms; "
                f"next voice free in {deficit_ms:.1f}ms")


def plan_score(
    score: Score,
    instruments: dict[str, Instrument],
    binding: dict[int, list[str]],
    tolerance_ms: float = DEFAULT_TOLERANCE_MS,
    tempo_scale: float = 1.0,
) -> Plan:
    """Assign every note in the score to a voice on a bot.

    binding maps a part_id to the bots that may play it, most preferred first.
    Listing more than one bot lets a part fall back, which is how two snare bots
    give you four sticks instead of two.

    tempo_scale multiplies note times: 0.5 plays twice as fast.
    """
    if tolerance_ms < 0:
        raise PlanError("tolerance_ms cannot be negative")
    if tempo_scale <= 0:
        raise PlanError("tempo_scale must be positive")

    for part_id, bot_ids in binding.items():
        for bot_id in bot_ids:
            if bot_id not in instruments:
                raise PlanError(f"part {part_id} is bound to unknown bot {bot_id!r}")

    state = {bot_id: BotState(inst) for bot_id, inst in instruments.items()}
    tolerance_s = tolerance_ms / 1000.0
    plan = Plan(tempo_scale=tempo_scale)

    # One pass over every note in time order, so bots shared between parts see
    # a single consistent view of when their voices are busy.
    for event in sorted(score.events, key=lambda e: (e.time_s, e.part_id, e.note)):
        requested_s = event.time_s * tempo_scale
        bot_ids = binding.get(event.part_id, [])

        if not bot_ids:
            plan.drops.append(Drop(event.part_id, event.note, requested_s,
                                   "no_bot_for_part", "part is not bound to any bot"))
            continue

        placed = False
        near_miss: tuple[str, str] | None = None
        accepted_anywhere = False

        for bot_id in bot_ids:
            bot = state[bot_id]
            slot = bot.earliest(event.note, requested_s)
            if slot is None:
                continue
            accepted_anywhere = True
            voice, at_s = slot

            if at_s - requested_s <= tolerance_s:
                bot.commit(voice, at_s)
                plan.hits.append(ScheduledHit(
                    part_id=event.part_id,
                    bot_id=bot_id,
                    voice=voice,
                    note=event.note,
                    velocity=event.velocity,
                    play_at_s=at_s,
                    requested_s=requested_s,
                    first_choice_bot=bot_ids[0],
                ))
                placed = True
                break

            if near_miss is None:
                near_miss = bot.blocking_reason(event.note, requested_s, at_s)

        if placed:
            continue

        if not accepted_anywhere:
            plan.drops.append(Drop(
                event.part_id, event.note, requested_s, "note_not_accepted",
                f"no bound bot plays note {event.note}"))
        else:
            reason, detail = near_miss or ("cycle_not_ready", "")
            plan.drops.append(Drop(event.part_id, event.note, requested_s, reason, detail))

    return plan


def max_feasible_scale(
    score: Score,
    instruments: dict[str, Instrument],
    binding: dict[int, list[str]],
    tolerance_ms: float = DEFAULT_TOLERANCE_MS,
    lowest: float = 0.2,
    steps: int = 24,
) -> float:
    """Smallest tempo_scale (so fastest tempo) that still drops nothing.

    Feasibility is monotonic in scale: stretching time never creates a conflict
    that was not already there, so a bisection is safe.
    """
    if plan_score(score, instruments, binding, tolerance_ms, 1.0).feasible:
        # Already fits as written; find how much faster it could go.
        if plan_score(score, instruments, binding, tolerance_ms, lowest).feasible:
            # Still fine at the fastest scale we search. The real limit is
            # somewhere beyond it, so this is a lower bound, not an answer.
            return lowest
        lo, hi = lowest, 1.0
        for _ in range(steps):
            mid = (lo + hi) / 2
            if plan_score(score, instruments, binding, tolerance_ms, mid).feasible:
                hi = mid
            else:
                lo = mid
        return hi

    lo, hi = 1.0, 1.0
    for _ in range(8):
        hi *= 2
        if plan_score(score, instruments, binding, tolerance_ms, hi).feasible:
            break
    else:
        return float("inf")

    for _ in range(steps):
        mid = (lo + hi) / 2
        if plan_score(score, instruments, binding, tolerance_ms, mid).feasible:
            hi = mid
        else:
            lo = mid
    return hi
