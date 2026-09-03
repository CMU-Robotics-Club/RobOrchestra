"""Drive the existing Arduino daisy chain, with no firmware changes at all.

The old bots have no clock and no buffer. A note plays when its bytes arrive,
so everything the new design pushes down to the bot has to be done up here
instead: this transport holds each hit until it is time, subtracts the bot's
mechanical latency itself, and translates General MIDI note numbers into
whatever each board was actually flashed to listen for.

That is the whole point of writing it. The planner, the player and the score
format all run unchanged against hardware that is up to six years old, so the
new stack can be proved on the orchestra that already exists rather than on one
that has to be built first.

Two things it does better than the Processing sketches it replaces:

- Ports are matched by name, not by index. `new MidiBus(this, 0, 3)` picks a
  different device depending on the laptop and the order things were plugged
  in, which is most of what the wiki's Debugging page is about.
- Nothing sleeps between sends. InteractiveDemoCONDUCTING.pde calls delay(2)
  twice to dodge buffer collisions, which bakes about 4 ms of skew into every
  beat. DIN costs 0.96 ms per note-on and that is unavoidable, but there is no
  reason to add to it.
"""

from __future__ import annotations

import heapq
import logging
import threading
import time
from collections.abc import Iterable

from ..core.plan import Instrument, ScheduledHit
from .base import Transport

logger = logging.getLogger(__name__)

# 31250 baud, 8N1, three bytes per note-on.
DIN_BYTE_S = 10 / 31250
NOTE_ON_S = 3 * DIN_BYTE_S

POLL_S = 0.001
DEFAULT_VELOCITY = 100

# When several hits fall together, the wire can only carry one at a time. Low
# sounds are perceived as arriving slightly later than high ones at the same
# physical onset, so putting them first spends the unavoidable serialisation
# where it does least damage.
ROLE_ORDER = {"bass": 0, "kick": 0, "tom": 1, "snare": 2, "xylo": 3}


class LegacyDinTransport(Transport):
    """Sends plain MIDI to bots that cannot schedule anything themselves."""

    name = "legacy_din"

    def __init__(
        self,
        instruments: dict[str, Instrument],
        port_name: str | None = None,
        port=None,
        note_map: dict[str, dict[int, int]] | None = None,
        channels: dict[str, int] | None = None,
        lookahead_s: float = 0.25,
        send_velocity: bool = False,
        clock=None,
    ):
        self._instruments = instruments
        self._note_map = note_map or {}
        self._channels = channels or {}
        self._requested_port = port_name
        self._port = port
        self._owns_port = port is None
        self._lookahead_s = lookahead_s
        self._send_velocity = send_velocity
        self._clock = clock

        self._queue: list[tuple[float, int, ScheduledHit]] = []
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._running = threading.Event()
        self._thread: threading.Thread | None = None
        self._origin: float | None = None
        self._seq = 0

        self.sent = 0
        self.late = 0
        self.worst_late_ms = 0.0

        # A note at score time zero has to go on the wire before the piece
        # starts, by however long that bot takes to travel. Push time zero
        # forward by the largest such head start so the downbeat is reachable.
        self.lead_in_s = max(
            (inst.model.mech_latency_ms / 1000.0 for inst in instruments.values()),
            default=0.0,
        )

    # port selection

    @staticmethod
    def list_ports() -> list[str]:
        try:
            import mido
        except Exception:
            return []
        return list(mido.get_output_names())

    @staticmethod
    def resolve_port(available: list[str], requested: str | None) -> str | None:
        """Match a port by exact name, then by substring, case insensitively.

        Replaces picking a device by index, which is the single most common way
        a rehearsal starts twenty minutes late.
        """
        if not available:
            return None
        if requested:
            if requested in available:
                return requested
            lowered = requested.lower()
            for name in available:
                if lowered in name.lower():
                    return name
            return None
        for hint in ("usb-midi", "usb midi", "roborchestra", "arduino"):
            for name in available:
                if hint in name.lower():
                    return name
        return available[0]

    # timing

    @property
    def lookahead_s(self) -> float:
        return self._lookahead_s

    def live_lead_s(self, bot_id: str) -> float:
        # A live strike goes on the wire now; the earliest it can sound is one
        # mechanical travel away. Using lookahead_s here would add a quarter
        # second of pure lag, because that number is a planning window, not a
        # physical constraint.
        inst = self._instruments.get(bot_id)
        return (inst.model.mech_latency_ms / 1000.0) if inst else 0.0

    @property
    def now_s(self) -> float:
        if self._origin is None:
            return 0.0
        return (self._clock or time.monotonic)() - self._origin

    def _send_at(self, hit: ScheduledHit) -> float:
        """When to put this hit on the wire.

        The bot cannot compensate for its own travel time, so it is taken off
        here. On the new firmware this subtraction moves into the bot, where it
        belongs, and this line goes away.
        """
        inst = self._instruments.get(hit.bot_id)
        mech_s = (inst.model.mech_latency_ms / 1000.0) if inst else 0.0
        return hit.play_at_s - mech_s

    def _order_key(self, hit: ScheduledHit) -> int:
        inst = self._instruments.get(hit.bot_id)
        return ROLE_ORDER.get(inst.role if inst else "", 99)

    # translation

    def wire_note(self, hit: ScheduledHit) -> int:
        return self._note_map.get(hit.bot_id, {}).get(hit.note, hit.note)

    def wire_channel(self, hit: ScheduledHit) -> int:
        return self._channels.get(hit.bot_id, 0)

    # lifecycle

    def start(self) -> None:
        if self._thread is not None:
            return
        if self._port is None:
            import mido

            available = self.list_ports()
            name = self.resolve_port(available, self._requested_port)
            if name is None:
                raise RuntimeError(
                    f"no MIDI output matched {self._requested_port!r}. "
                    f"Available: {', '.join(available) or 'none'}"
                )
            self._port = mido.open_output(name)
            logger.info("legacy_din using MIDI output %s", name)

        self._origin = (self._clock or time.monotonic)() + self.lead_in_s
        self._stop.clear()
        self._running.clear()
        self._thread = threading.Thread(target=self._run, name="legacy-din", daemon=True)
        self._thread.start()
        # Wait for the sender to actually be running. Without this the first
        # hit goes out however long the thread took to spin up late, which is
        # about 20 ms and lands on a downbeat.
        if not self._running.wait(timeout=2.0):
            raise RuntimeError("legacy_din sender thread did not start")

    def send(self, hits: Iterable[ScheduledHit]) -> int:
        n = 0
        with self._lock:
            for hit in hits:
                heapq.heappush(self._queue, (self._send_at(hit), self._seq, hit))
                self._seq += 1
                n += 1
        if n:
            self._wake.set()
        return n

    def _run(self) -> None:
        self._running.set()
        while not self._stop.is_set():
            now = self.now_s
            due = []
            with self._lock:
                while self._queue and self._queue[0][0] <= now:
                    due.append(heapq.heappop(self._queue))

            if due:
                # Everything in this batch was meant for the same instant or
                # earlier, so order it deliberately rather than by heap order.
                due.sort(key=lambda item: (item[0], self._order_key(item[2])))
                for send_at, _seq, hit in due:
                    behind_ms = (now - send_at) * 1000.0
                    if behind_ms > 2.0:
                        self.late += 1
                        self.worst_late_ms = max(self.worst_late_ms, behind_ms)
                    self._emit(hit)
                continue

            self._wake.wait(POLL_S)
            self._wake.clear()

    def _emit(self, hit: ScheduledHit) -> None:
        if self._port is None:
            return
        import mido

        velocity = hit.velocity if self._send_velocity else DEFAULT_VELOCITY
        self._port.send(mido.Message(
            "note_on",
            channel=self.wire_channel(hit),
            note=self.wire_note(hit),
            velocity=max(1, min(127, velocity)),
        ))
        self.sent += 1

    def panic(self) -> None:
        """Silence everything. Safe to call at any time, including on the way out."""
        if self._port is None:
            return
        import mido

        for channel in range(16):
            try:
                self._port.send(mido.Message("control_change", channel=channel,
                                             control=123, value=0))
            except Exception:
                logger.warning("panic failed on channel %s", channel, exc_info=True)

    def close(self) -> None:
        self._stop.set()
        self._wake.set()
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self.panic()
        if self._port is not None and self._owns_port:
            self._port.close()
        self._port = None

    @property
    def pending(self) -> int:
        with self._lock:
            return len(self._queue)


def wire_time_s(simultaneous_notes: int) -> float:
    """How long this many note-ons take to serialise on a DIN cable.

    Worth being able to quote: a six note chord smears over about 5.8 ms no
    matter how good the scheduling is, which is a hardware argument for moving
    off the daisy chain rather than a software one.
    """
    return simultaneous_notes * NOTE_ON_S
