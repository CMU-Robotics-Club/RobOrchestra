"""Grooves that are made up, not looked up.

The classic engine picks one of three patterns and plays it until told
otherwise, which is why it sounds like a drum machine. This generator
decides each bar from what the music is doing, on rules a drummer would
recognise:

- Some hits are not decisions. A kick opens every group of the bar, the
  snare answers it (the backbeat in 4, beat three in a waltz), and those
  never go anywhere: the groove keeps its identity however busy or sparse
  it gets.
- Everything else is a probability shaped by one knob, *activity*: offbeat
  kicks, the push into the next group, a sixteenth pickup, ghost snares,
  a tom ghost before the backbeat. Each bar rolls the dice again — but only
  for a quarter of the optional slots, so the groove evolves rather than
  churns. Two bars are rarely identical and never unrelated.
- The piece's shape gets its due. The last beat of a phrase carries a fill,
  a bigger one closes a period, the first bar of a new section opens with
  an accent, and a beat where the harmony is expected to move gets a kick
  it might not otherwise have had.
- A fill can answer the pianist: given the rhythm of their last bar, the
  fill plays that rhythm on toms and snare instead of something generic.
- Dynamics are continuous. Every velocity is scaled by the gain read off
  the pianist, and the beats the pianist accents get accented.
- Swing is read, not assumed: offbeats go where the pianist's offbeats go,
  and straight sixteenths stay out of a swing feel.

Physical floors are respected before anything is asked for, as in the
classic engine, so a busier bar never asks a bot for what it cannot do.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .groove import ScheduledNote, check_grouping, default_grouping

KICK, SNARE, TOM = 36, 38, 45
NOTE_OF = {"K": KICK, "S": SNARE, "T": TOM}
BASE_VELOCITY = {"K": 100, "S": 104, "T": 92}

GHOST = 0.55                # velocity factor for ghost notes
FILL_VELOCITY = 0.92
SECTION_ACCENT = 1.15
CHANGE_ACCENT = 1.05
MUTATE = 0.25               # share of optional slots re-rolled each bar
# The knobs a player reaches for. Decoration scales every optional hit's
# probability — 0 is the plain beat, 1 is everything activity can buy —
# and the default sits at half because a steady beat with riffs between
# is what most people mean by "drums", and a kit that decorates every
# beat feels like all riffs. Riffs says where the fills go: every phrase
# end (and a bigger one at a period end), only period ends, or nowhere but
# the holes the pianist leaves and the fill command.
DECORATION = 0.5
RIFFS = ("phrase", "period", "none")
SWING_ON = 0.56             # above this the "and" goes to the swing point, and sixteenths go
FILL_DENSITY_BASE = 0.45
FILL_DENSITY_PER_ACTIVITY = 0.5


@dataclass(frozen=True)
class BeatContext:
    """Everything the generator wants to know about one beat."""

    time_s: float
    period_s: float
    beat_in_bar: int            # 1-based
    bar_index: int
    bar_in_phrase: int = 0
    phrase_end: bool = False
    hyper_end: bool = False
    section_started: bool = False
    activity: float = 0.5
    gain: float = 1.0
    accent: float = 1.0         # how much the pianist accents this beat, around 1.0
    swing: float = 0.5
    chord_change: bool = False  # the harmony is expected to move on this beat
    echo: tuple[int, ...] = ()  # sixteenth positions (0..) of the pianist's last bar
    fill_requested: bool = False


class PhysicalFloors:
    """Drop notes the shared hardware could never land, earliest wins."""

    def __init__(self, kt_min_gap_s: float = 0.0, snare_min_gap_s: float = 0.0) -> None:
        self._kt = max(float(kt_min_gap_s), 0.0)
        self._snare = max(float(snare_min_gap_s), 0.0)
        self._last_kt: float | None = None
        self._last_snare: float | None = None
        self.thinned = 0

    def thin(self, notes: list[ScheduledNote]) -> list[ScheduledNote]:
        if not self._kt and not self._snare:
            return notes
        kept: list[ScheduledNote] = []
        for note in sorted(notes, key=lambda n: n.time_s):
            snare = note.note == SNARE
            last = self._last_snare if snare else self._last_kt
            gap = self._snare if snare else self._kt
            if last is not None and note.time_s < last - 1.0:
                self._last_kt = self._last_snare = None   # the grid jumped back
                last = None
            if last is not None and gap and note.time_s - last < gap:
                self.thinned += 1
                continue
            if snare:
                self._last_snare = note.time_s
            else:
                self._last_kt = note.time_s
            kept.append(note)
        return kept


Slot = tuple[int, int, str]     # (beat 0-based, sixteenth 0..3, voice)


def slot_probabilities(grouping: tuple[int, ...], activity: float) -> dict[Slot, float]:
    """Every hit the bar might carry and how likely it is, for this activity.

    A probability of 1.0 is a hit the groove is built on; the rest are the
    decorations activity buys.
    """
    a = max(0.0, min(1.0, activity))
    p: dict[Slot, float] = {}
    beats = sum(grouping)
    pos = 0
    for length in grouping:
        p[(pos, 0, "K")] = 1.0
        if length == 4:
            p[(pos + 2, 0, "K")] = 0.9
            p[(pos + 1, 0, "S")] = 1.0
            p[(pos + 3, 0, "S")] = 1.0
        elif length == 3:
            p[(pos + 2, 0, "S")] = 1.0
            p[(pos + 1, 0, "S")] = 0.35 + 0.4 * a
        elif length == 2:
            p[(pos + 1, 0, "S")] = 1.0
        last = pos + length - 1
        for b in range(pos, pos + length):
            p.setdefault((b, 2, "K"), (0.15 + 0.5 * a) if b == last else (0.1 + 0.3 * a))
        pickup = (pos - 1) % beats
        p.setdefault((pickup, 3, "K"), 0.25 * a)
        pos += length
    for b in range(beats):
        if p.get((b, 0, "S"), 0.0) < 1.0:
            p.setdefault((b, 1, "S"), 0.35 * a)
            p.setdefault((b, 3, "S"), 0.3 * a)
        if p.get(((b + 1) % beats, 0, "S"), 0.0) >= 1.0:
            p.setdefault((b, 3, "T"), 0.35 * a)
    return p


class GrooveGenerator:
    """Beat contexts in, drum notes out; keeps a bar's identity between beats."""

    def __init__(
        self,
        beats_per_bar: int = 4,
        grouping: tuple[int, ...] | None = None,
        rng_seed: int | None = None,
        kt_min_gap_s: float = 0.0,
        snare_min_gap_s: float = 0.0,
        decoration: float = DECORATION,
        riffs: str = "phrase",
        mutation: float = MUTATE,
    ) -> None:
        self._rng = random.Random(rng_seed)
        self._floors = PhysicalFloors(kt_min_gap_s, snare_min_gap_s)
        self._decoration = DECORATION
        self._riffs = "phrase"
        self._mutation = MUTATE
        self.set_decoration(decoration)
        self.set_riffs(riffs)
        self.set_mutation(mutation)
        self._beats_per_bar = 0
        self._grouping: tuple[int, ...] = ()
        self.set_meter(beats_per_bar, grouping)
        self._on: dict[Slot, bool] = {}
        self._bar_rolled: int | None = None
        self._fill_pending = False
        self.bars = 0

    @property
    def beats_per_bar(self) -> int:
        return self._beats_per_bar

    @property
    def grouping(self) -> tuple[int, ...]:
        return self._grouping

    @property
    def thinned(self) -> int:
        return self._floors.thinned

    @property
    def decoration(self) -> float:
        return self._decoration

    @property
    def riffs(self) -> str:
        return self._riffs

    @property
    def mutation(self) -> float:
        return self._mutation

    def set_decoration(self, value: float) -> None:
        """How much of the optional playing to do, 0 (plain beat) to 1."""
        self._decoration = max(0.0, min(1.0, float(value)))

    def set_riffs(self, value: str) -> None:
        value = str(value).strip().lower()
        if value not in RIFFS:
            raise ValueError(f"riffs must be one of {', '.join(RIFFS)}, not {value!r}")
        self._riffs = value

    def set_mutation(self, value: float) -> None:
        """Share of the optional slots re-rolled each bar; 0 repeats the bar."""
        self._mutation = max(0.0, min(1.0, float(value)))

    def set_meter(self, beats_per_bar: int, grouping: tuple[int, ...] | None = None) -> None:
        if beats_per_bar < 1:
            raise ValueError("beats_per_bar must be at least 1")
        groups = tuple(grouping) if grouping else default_grouping(int(beats_per_bar))
        check_grouping(groups, int(beats_per_bar))
        self._beats_per_bar = int(beats_per_bar)
        self._grouping = groups
        self._on = {}
        self._bar_rolled = None

    def request_fill(self) -> None:
        self._fill_pending = True

    def _roll_bar(self, activity: float, bar_index: int) -> None:
        """Decide the optional hits for a bar: keep most, re-roll a few."""
        probs = slot_probabilities(self._grouping, activity)
        fresh = self._bar_rolled is None or not self._on
        for slot, p in probs.items():
            if p >= 1.0:
                self._on[slot] = True
            elif fresh or slot not in self._on or self._rng.random() < self._mutation:
                self._on[slot] = self._rng.random() < p * self._decoration
        for slot in list(self._on):
            if slot not in probs:
                del self._on[slot]
        self._bar_rolled = bar_index
        self.bars += 1

    def notes_for_beat(self, ctx: BeatContext) -> list[ScheduledNote]:
        if ctx.beat_in_bar == 1 or self._bar_rolled != ctx.bar_index:
            self._roll_bar(ctx.activity, ctx.bar_index)
        beat = ctx.beat_in_bar - 1
        last_beat = beat == self._beats_per_bar - 1
        swung = ctx.swing >= SWING_ON
        sub_times = self._sub_times(ctx, swung)

        fill = self._fill_pending and last_beat
        if self._riffs == "phrase":
            fill = fill or (ctx.phrase_end and last_beat)
        if self._riffs in ("phrase", "period"):
            fill = fill or (ctx.hyper_end and beat >= self._beats_per_bar - 2)
        if fill and last_beat and self._fill_pending:
            self._fill_pending = False

        notes: list[tuple[float, str, float, str]] = []   # (time, voice, factor, source)
        if fill:
            notes += self._fill(ctx, beat, sub_times, swung)
        else:
            for (b, sub, voice), on in self._on.items():
                if b != beat or not on:
                    continue
                if swung and sub in (1, 3):
                    continue
                factor = GHOST if sub in (1, 3) else 1.0
                if sub == 0:
                    factor *= ctx.accent
                notes.append((sub_times[sub], voice, factor, "groove"))
            if (ctx.chord_change and self._rng.random() < self._decoration
                    and not any(v == "K" and t == sub_times[0] for t, v, _, _ in notes)):
                notes.append((sub_times[0], "K", ctx.accent, "groove"))
            if ctx.chord_change and self._rng.random() < 0.5 * self._decoration:
                notes.append((sub_times[0], "T", CHANGE_ACCENT * ctx.accent, "groove"))
        if ctx.section_started and beat == 0:
            notes.append((sub_times[0], "T", SECTION_ACCENT, "section"))
            if not any(v == "S" and t == sub_times[0] for t, v, _, _ in notes):
                notes.append((sub_times[0], "S", SECTION_ACCENT, "section"))

        out: list[ScheduledNote] = []
        seen: set[tuple[float, str]] = set()
        for t, voice, factor, source in notes:
            key = (round(t, 4), voice)
            if key in seen:
                continue
            seen.add(key)
            velocity = round(BASE_VELOCITY[voice] * factor * ctx.gain)
            out.append(ScheduledNote(time_s=t, note=NOTE_OF[voice],
                                     velocity=max(1, min(127, velocity)), source=source))
        return self._floors.thin(out)

    def _sub_times(self, ctx: BeatContext, swung: bool) -> tuple[float, float, float, float]:
        period = ctx.period_s
        and_at = ctx.swing if swung else 0.5
        return (ctx.time_s, ctx.time_s + 0.25 * period,
                ctx.time_s + and_at * period, ctx.time_s + 0.75 * period)

    def _fill(self, ctx: BeatContext, beat: int, sub_times, swung: bool):
        """The fill for one beat: the pianist's rhythm if we have it, else rolled."""
        subs = (0, 2) if swung else (0, 1, 2, 3)
        positions: list[int] = []
        if ctx.echo:
            positions = [s for s in subs if (beat * 4 + s) in ctx.echo]
            if not positions:
                positions = [0]
        else:
            density = FILL_DENSITY_BASE + FILL_DENSITY_PER_ACTIVITY * ctx.activity
            positions = [s for s in subs if s == 0 or self._rng.random() < density]
        notes = []
        voice = "S" if (beat + len(positions)) % 2 == 0 else "T"
        for i, sub in enumerate(positions):
            v = "S" if (voice == "S") == (i % 2 == 0) else "T"
            closing = beat == self._beats_per_bar - 1 and sub == positions[-1]
            factor = 1.0 if closing else FILL_VELOCITY
            notes.append((sub_times[sub], v, factor, "fill"))
        if beat == 0 or ctx.hyper_end:
            notes.append((sub_times[0], "K", 1.0, "fill"))
        return notes
