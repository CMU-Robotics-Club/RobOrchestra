"""Run a recorded piano session through the jam pipeline, offline and fast.

A session recorded with `tutti jam --record` is the only kind of evidence
that says what the tracker does with real hands, and it should be usable
without the hands: replayed on a hand-cranked clock, in a fraction of a
second, with the same code path a live session takes. That makes a
recording a regression fixture — change the tracker, replay every session,
see what moved — and a diagnostic: a second-by-second account of what the
tracker believed while the pianist played.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.ensemble import Ensemble
from ..core.fleet import DEFAULT_FLEET
from ..transports.loopback import NullTransport
from .jam import JamSource
from .midi_in import NoteOn


@dataclass(frozen=True)
class Snapshot:
    """The tracker's state at one instant of the replay."""

    t_s: float
    bpm: float | None
    confidence: float
    locked: bool
    beat_in_bar: int
    mode: str
    intensity: int
    hits: int
    alternatives: tuple[float, ...]
    rubato: float
    gap_fills: int = 0
    velocity_scale: float = 1.0
    activity: float = 0.0
    section: int = 0
    chord: str = ""
    key: str = ""


@dataclass
class Replay:
    events: int
    duration_s: float
    snapshots: list[Snapshot]
    hits: list
    first_lock_s: float | None

    @property
    def locked_fraction(self) -> float:
        """How much of the time after the first onset the tracker was locked."""
        if not self.snapshots:
            return 0.0
        return sum(1 for s in self.snapshots if s.locked) / len(self.snapshots)


def replay_session(
    events: list[NoteOn],
    fleet=None,
    snapshot_every_s: float = 1.0,
    tail_s: float = 2.0,
    step_s: float = 0.005,
    **jam_kwargs,
) -> Replay:
    """Feed recorded note-ons through a JamSource on a synthetic clock."""
    if fleet is None:
        fleet = {k: v for k, v in DEFAULT_FLEET.items() if v.role in ("snare", "tom")}
    clock = [0.0]
    transport = NullTransport()
    ensemble = Ensemble(fleet, transport, clock=lambda: clock[0])
    source = JamSource(**jam_kwargs)
    source.bind(ensemble)

    pending = sorted(events, key=lambda e: e.t_s)
    end = (pending[-1].t_s if pending else 0.0) + tail_s
    snapshots: list[Snapshot] = []
    next_snapshot = 0.0
    first_lock = None
    i = 0
    while clock[0] <= end:
        while i < len(pending) and pending[i].t_s <= clock[0]:
            source._on_note(pending[i])
            i += 1
        source._tick(clock[0])
        state = source.beat_state
        if state.locked and first_lock is None:
            first_lock = clock[0]
        if clock[0] >= next_snapshot:
            next_snapshot += snapshot_every_s
            snapshots.append(Snapshot(
                t_s=clock[0], bpm=state.bpm, confidence=state.confidence,
                locked=state.locked, beat_in_bar=state.beat_in_bar,
                mode=source.mode, intensity=source.intensity,
                hits=len(transport.received), alternatives=state.alternatives,
                rubato=state.rubato, gap_fills=source.gap_fills,
                velocity_scale=source.feel.velocity_scale if source.feel else 1.0,
                activity=source.activity,
                section=source.phrase_context.section if source.phrase_context else 0,
                chord=(source.harmony_state.chord.name
                       if source.harmony_state and source.harmony_state.chord else ""),
                key=source.harmony_state.key_name if source.harmony_state else "",
            ))
        clock[0] += step_s

    return Replay(
        events=len(pending), duration_s=end, snapshots=snapshots,
        hits=list(transport.received), first_lock_s=first_lock,
    )


def describe(replay: Replay) -> list[str]:
    """A readable account of a replay, one line per snapshot plus a summary."""
    lines = []
    for s in replay.snapshots:
        bpm = f"{s.bpm:6.1f}" if s.bpm else "  --.-"
        line = (f"t={s.t_s:5.1f}s bpm={bpm} conf={s.confidence:.2f} "
                f"lock={'Y' if s.locked else 'n'} beat={s.beat_in_bar} "
                f"{s.mode}/{s.intensity} hits={s.hits}")
        if s.alternatives:
            line += " alt=" + "/".join(f"{b:.0f}" for b in s.alternatives[:2])
        if abs(s.rubato - 1.0) > 0.03:
            line += f" rubato={s.rubato - 1.0:+.0%}"
        if s.locked:
            line += f" act={s.activity:.2f} sec={s.section}"
        if s.chord:
            line += f" {s.chord}/{s.key}"
        if s.velocity_scale < 1.0:
            line += f" fading={s.velocity_scale:.2f}"
        if s.gap_fills:
            line += f" fills={s.gap_fills}"
        lines.append(line)
    lock = f"{replay.first_lock_s:.1f}s" if replay.first_lock_s is not None else "never"
    lines.append(f"{replay.events} notes over {replay.duration_s:.1f}s: first lock {lock}, "
                 f"locked {replay.locked_fraction:.0%} of the time, {len(replay.hits)} hits")
    return lines
