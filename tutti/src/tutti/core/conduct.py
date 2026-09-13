"""Follow a human conductor: strokes in, a clock that runs in beats out.

The old Processing demo counted baton beats seen by a Pixy camera over a
three second window and turned the count into a BPM. That gives a tempo, but
not a phase: the notes never knew *which* beat they were on, so the music
could not be conducted, only sped up and slowed down. This module keeps both.

Every accepted stroke is a beat with a number. Time between strokes is the
period, followed with inertia so an accelerando is tracked without a single
rushed stroke yanking the tempo. The clock then answers one question for
whatever is playing: "when does beat b fall?" Beats up to one past the last
stroke are predicted from the flywheel, which is how the notes *on* the next
beat get scheduled early enough for a stick to be moving before the baton
lands. Beats beyond that are not predicted at all — a piece follows the
conductor, so if the conductor stops, it stops on the next beat, and picks up
where it left off on the next stroke. That is a fermata, and it comes for
free from refusing to guess.

Two kinds of bad stroke are named rather than followed. A stroke inside
half a period of the last is the camera seeing one gesture twice, and is
ignored. A stroke about two periods out is a stroke the camera missed, and
the beat count jumps to keep the orchestra with the conductor rather than a
beat behind for the rest of the piece.

Pure and clockless: every time is on the caller's clock, and nothing here
sleeps or threads, so it can be driven by a test as fast as it likes.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor

from .score import NoteEvent, Score

MIN_PERIOD_S = 0.25         # 240 BPM; faster than this is a bounce, not a beat
MAX_PERIOD_S = 2.0          # 30 BPM; slower and the count-in starts over
BOUNCE_RATIO = 0.45         # a stroke this soon after the last is the same stroke
MISSED_RATIO = 1.6          # beyond this the camera probably missed one
RESUME_RATIO = 2.5          # beyond this the conductor had stopped
PERIOD_ALPHA = 0.5          # how much of a new interval the tempo takes on
PHASE_GAIN = 0.7            # how much of a stroke's timing error the grid takes on
HOLD_RATIO = 1.5            # reported as holding once a stroke is this overdue
DYNAMICS_ALPHA = 0.5
DYNAMICS_INITIAL = 0.6

STROKE_KINDS = ("count_in", "beat", "bounce", "missed", "resume", "restart")


@dataclass(frozen=True)
class Stroke:
    """What the clock made of one conductor stroke."""

    t_s: float
    kind: str
    beat: int | None = None         # the beat this stroke was taken to be
    period_s: float | None = None   # the tempo after this stroke


@dataclass(frozen=True)
class Note:
    """One note a program wants played, in General MIDI."""

    note: int
    velocity: int


class ConductorClock:
    """Turns conductor strokes into a beat-indexed clock."""

    def __init__(
        self,
        count_in: int = 4,
        min_period_s: float = MIN_PERIOD_S,
        max_period_s: float = MAX_PERIOD_S,
        period_alpha: float = PERIOD_ALPHA,
        phase_gain: float = PHASE_GAIN,
        coast_beats: int = 0,
    ) -> None:
        if count_in < 2:
            raise ValueError("count_in needs at least two strokes: one gap sets the tempo")
        if not 0.0 < min_period_s < max_period_s:
            raise ValueError("need 0 < min_period_s < max_period_s")
        if not 0.0 <= period_alpha <= 1.0 or not 0.0 <= phase_gain <= 1.0:
            raise ValueError("period_alpha and phase_gain are 0 to 1")
        if coast_beats < 0:
            raise ValueError("coast_beats cannot be negative")
        self._count_in = int(count_in)
        self._min_period = float(min_period_s)
        self._max_period = float(max_period_s)
        self._alpha = float(period_alpha)
        self._gain = float(phase_gain)
        self._coast = int(coast_beats)
        self.reset()

    def reset(self) -> None:
        self._period: float | None = None
        self._anchor_t: float | None = None
        self._anchor_beat: int = -self._count_in
        self._last_t: float | None = None
        self._dynamics = DYNAMICS_INITIAL
        self.strokes = 0
        self.bounces = 0
        self.last: Stroke | None = None

    # what the clock believes

    @property
    def count_in(self) -> int:
        return self._count_in

    @property
    def started(self) -> bool:
        """True once one interval has set a tempo."""
        return self._period is not None

    @property
    def period_s(self) -> float | None:
        return self._period

    @property
    def bpm(self) -> float | None:
        return 60.0 / self._period if self._period else None

    @property
    def anchor_beat(self) -> int:
        """The beat number of the last accepted stroke. Negative during the count-in."""
        return self._anchor_beat

    @property
    def last_stroke_s(self) -> float | None:
        return self._last_t

    @property
    def dynamics(self) -> float:
        """How big the strokes have been lately, 0 to 1."""
        return self._dynamics

    def holding(self, now_s: float) -> bool:
        """Whether the conductor has left the orchestra waiting on the next beat."""
        if self._period is None or self._last_t is None:
            return False
        return now_s - self._last_t > HOLD_RATIO * self._period

    # input

    def on_stroke(self, t_s: float, strength: float = 1.0) -> Stroke:
        """Feed one stroke, at the moment the baton lands. Returns what it was taken for."""
        t_s = float(t_s)
        if self._last_t is None:
            return self._accept(t_s, self._anchor_beat, "count_in", strength, gain=1.0)

        gap = t_s - self._last_t
        if self._period is None:
            if gap < self._min_period:
                return self._bounce(t_s)
            if gap > self._max_period:
                # Two strokes too far apart to be a tempo: whoever this is
                # has started again, and this is their first stroke.
                self.reset()
                return self._accept(t_s, self._anchor_beat, "restart", strength, gain=1.0)
            self._period = gap
            beat = self._anchor_beat + 1
            return self._accept(t_s, beat, self._kind_for(beat), strength, gain=1.0)

        ratio = gap / self._period
        if ratio < BOUNCE_RATIO:
            return self._bounce(t_s)
        if ratio > RESUME_RATIO:
            # A fermata. The orchestra stopped on the beat after the last
            # stroke (plus whatever it was allowed to coast), and this stroke
            # releases it from there at the tempo it had.
            beat = self._anchor_beat + 1 + self._coast
            return self._accept(t_s, beat, "resume", strength, gain=1.0)
        if ratio > MISSED_RATIO:
            # About two beats out: the camera missed one. Jump the count so
            # the orchestra stays with the conductor rather than a beat behind.
            beat = self._anchor_beat + max(2, round(ratio))
            return self._accept(t_s, beat, "missed", strength, gain=1.0)

        beat = self._anchor_beat + 1
        kind = self._kind_for(beat)
        # During the count-in every stroke is the tempo; after it, inertia.
        alpha = 1.0 if beat <= 0 else self._alpha
        gain = 1.0 if beat <= 0 else self._gain
        expected = self._anchor_t + self._period if self._anchor_t is not None else t_s
        self._period = min(self._max_period, max(self._min_period,
                                                 self._period + alpha * (gap - self._period)))
        return self._accept(t_s, beat, kind, strength, gain=gain, expected=expected)

    def _kind_for(self, beat: int) -> str:
        return "count_in" if beat < 0 else "beat"

    def _bounce(self, t_s: float) -> Stroke:
        self.bounces += 1
        stroke = Stroke(t_s=t_s, kind="bounce", period_s=self._period)
        self.last = stroke
        return stroke

    def _accept(self, t_s: float, beat: int, kind: str, strength: float, gain: float,
                expected: float | None = None) -> Stroke:
        if expected is not None and gain < 1.0:
            # The grid moves part of the way to the stroke: the beat the
            # orchestra was already playing toward is the reference, and a
            # stroke that lands off it is jitter first and tempo second.
            self._anchor_t = expected + gain * (t_s - expected)
        else:
            self._anchor_t = t_s
        self._anchor_beat = beat
        self._last_t = t_s
        self._dynamics += DYNAMICS_ALPHA * (max(0.0, min(1.0, float(strength))) - self._dynamics)
        self.strokes += 1
        stroke = Stroke(t_s=t_s, kind=kind, beat=beat, period_s=self._period)
        self.last = stroke
        return stroke

    # output

    def time_of_beat(self, beat: float) -> float | None:
        """When beat `beat` falls, or None if that is not the conductor's to say yet.

        Anything up to one beat past the last stroke (plus the coast) is
        predicted from the tempo. Beyond that the answer has to wait for the
        conductor: that is what makes the orchestra stop when they do.
        """
        if self._period is None or self._anchor_t is None:
            return None
        if beat > self._anchor_beat + 1 + self._coast + 1e-9:
            return None
        return self._anchor_t + (beat - self._anchor_beat) * self._period

    def next_beat_s(self) -> float | None:
        """When the next stroke is expected."""
        return self.time_of_beat(self._anchor_beat + 1)


def auto_offset_beats(first_beat: float, beats_per_bar: int) -> float:
    """Where to put beat 0 so the piece starts on the first stroke after the count-in.

    A note on a downbeat becomes beat 0. A note part way through a bar is a
    pickup: it lands *before* beat 0, inside the count-in, and the following
    downbeat is beat 0 — which is how anyone would count a piece in.
    """
    if beats_per_bar < 1:
        raise ValueError("beats_per_bar must be at least 1")
    downbeat = floor(first_beat / beats_per_bar + 1e-9) * beats_per_bar
    if abs(first_beat - downbeat) < 1e-6:
        return -downbeat
    return -(downbeat + beats_per_bar)


class ScoreProgram:
    """A score, handed out beat by beat in the order the conductor reaches it."""

    def __init__(
        self,
        score: Score,
        beat_unit: float = 1.0,
        offset_beats: float | str = "auto",
        beats_per_bar: int = 4,
        accepts: set[int] | None = None,
    ) -> None:
        if beat_unit <= 0:
            raise ValueError("beat_unit must be positive")
        if beats_per_bar < 1:
            raise ValueError("beats_per_bar must be at least 1")
        self.name = score.name
        self._beats_per_bar = int(beats_per_bar)
        playable: list[NoteEvent] = []
        self.unplayable = 0
        for event in score.events:
            if accepts is not None and event.note not in accepts:
                self.unplayable += 1
                continue
            playable.append(event)

        if playable:
            first = min(e.beat for e in playable) / beat_unit
            if offset_beats == "auto":
                offset = auto_offset_beats(first, self._beats_per_bar)
            else:
                offset = float(offset_beats)
        else:
            offset = 0.0
        self.offset_beats = offset

        groups: dict[float, list[Note]] = {}
        for event in playable:
            beat = round(event.beat / beat_unit + offset, 6)
            groups.setdefault(beat, []).append(Note(event.note, event.velocity))
        self._groups: list[tuple[float, list[Note]]] = sorted(groups.items())
        self._cursor = 0

    @property
    def finished(self) -> bool:
        return self._cursor >= len(self._groups)

    @property
    def notes(self) -> int:
        return sum(len(notes) for _, notes in self._groups)

    @property
    def last_beat(self) -> float:
        return self._groups[-1][0] if self._groups else 0.0

    @property
    def first_beat(self) -> float:
        return self._groups[0][0] if self._groups else 0.0

    def next_beat(self) -> float | None:
        if self.finished:
            return None
        return self._groups[self._cursor][0]

    def pop_next(self) -> list[Note]:
        if self.finished:
            return []
        notes = self._groups[self._cursor][1]
        self._cursor += 1
        return notes

    def reset(self) -> None:
        self._cursor = 0

    def describe(self) -> str:
        beat = self._groups[min(self._cursor, len(self._groups) - 1)][0] if self._groups else 0.0
        bars = int(self.last_beat // self._beats_per_bar) + 1
        if self.finished:
            return f"done ({bars} bars)"
        bar = int(floor(beat / self._beats_per_bar))
        if bar < 0:
            return f"pickup, {bars} bars to go"
        return f"bar {bar + 1}/{bars}"
