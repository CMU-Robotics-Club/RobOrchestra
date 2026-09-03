"""Turn predicted beats into drum notes worth playing.

Ported from DrumBot/jam/groove_engine.py, then generalised. The original had
three hand-written 16-step patterns for 4/4. Those tables are now the output
of a small rule set applied to a *grouping* — how the bar's beats clump, so
4/4 is (4,), a waltz is (3,), Take Five is (3, 2) — which is how drummers
actually think about odd meters: not "five beats" but "three then two". A
kick opens every group, the snare answers inside it, and the three modes
add their offbeat kicks and tom ghosts relative to those snares. Applied to
(4,) the rules reproduce the old tables byte for byte, which the tests hold
them to, so nothing anyone tuned by ear in 4/4 has changed.

Fills land on whatever the bar's last beat is, overlaying that beat directly
instead of being spliced into a fixed-length list.

The note numbers are General MIDI and deliberately only three: kick, snare,
tom. There is no kick bot; 36 rides on the tom bot exactly as the firmware's
ROUTE_BD_TO_TOM does, and nothing here ever asks for a xylophone note, so
excluding Xylobot is structural rather than a filter someone can forget.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .beat import BeatEvent

_NOTE_MAP = {
    "K": 36,  # kick (rides on the tom bot)
    "S": 38,  # snare
    "T": 45,  # tom
}

_MODE_SET = ("groove", "sparse", "busy")

# Fills stay home when the tracker is not sure where the bar is; a fill in
# the wrong place is worse than no fill.
FILL_CONFIDENCE = 0.60

# How a bar of each length clumps unless told otherwise. 3+2 is the common
# 5/4 (Take Five, Mission: Impossible); 4+3 the common 7/4 (Money).
DEFAULT_GROUPINGS = {2: (2,), 3: (3,), 4: (4,), 5: (3, 2), 6: (3, 3), 7: (4, 3)}
MAX_GROUP = 4


def default_grouping(beats_per_bar: int) -> tuple[int, ...]:
    if beats_per_bar in DEFAULT_GROUPINGS:
        return DEFAULT_GROUPINGS[beats_per_bar]
    groups: list[int] = []
    left = beats_per_bar
    while left > 0:
        take = min(MAX_GROUP, left)
        groups.append(take)
        left -= take
    return tuple(groups)


def parse_grouping(text: str, beats_per_bar: int) -> tuple[int, ...]:
    """'3+2' -> (3, 2), checked against the bar it has to fill."""
    try:
        groups = tuple(int(part) for part in text.replace(" ", "").split("+"))
    except ValueError as exc:
        raise ValueError(f"grouping {text!r} is not like '3+2'") from exc
    check_grouping(groups, beats_per_bar)
    return groups


def check_grouping(groups: tuple[int, ...], beats_per_bar: int) -> None:
    if not groups or any(g < 1 or g > MAX_GROUP for g in groups):
        raise ValueError(f"grouping {groups} needs parts between 1 and {MAX_GROUP}")
    if sum(groups) != beats_per_bar:
        raise ValueError(f"grouping {groups} adds up to {sum(groups)}, "
                         f"not {beats_per_bar} beats")


def build_pattern(mode: str, intensity: int, grouping: tuple[int, ...]) -> list[str | None]:
    """One bar of sixteenth-note steps for this mode, intensity and grouping.

    The rules, in the order they apply:
    - Every group opens with a kick. A 2-group answers with a snare on its
      second beat, a 3-group on its third, a 4-group gets the backbeat (snare
      on 2 and 4, kick on 3). A 1-group is just its kick.
    - sparse plays only that, adding a kick an eighth before the last snare
      once intensity reaches 3.
    - groove adds that same pushing kick from intensity 2, and a tom on the
      last sixteenth from 3.
    - busy ghosts a tom on the sixteenth before every snare (from 2) and
      drives a kick an eighth after every snare, plus the closing tom from 3.
    - intensity 0 strips everything that is not on a beat.
    """
    steps = 4 * sum(grouping)
    pattern: list[str | None] = [None] * steps

    kicks: list[int] = []
    snares: list[int] = []
    beat = 0
    for length in grouping:
        s0 = beat * 4
        kicks.append(s0)
        if length == 2:
            snares.append(s0 + 4)
        elif length == 3:
            snares.append(s0 + 8)
        elif length == 4:
            kicks.append(s0 + 8)
            snares.extend((s0 + 4, s0 + 12))
        beat += length
    for s in kicks:
        pattern[s] = "K"
    for s in snares:
        pattern[s] = "S"
    last_snare = max(snares) if snares else None

    if mode == "sparse":
        if intensity >= 3 and last_snare is not None:
            pattern[last_snare - 2] = "K"
    elif mode == "groove":
        if intensity >= 2 and last_snare is not None:
            pattern[last_snare - 2] = "K"
        if intensity >= 3:
            pattern[steps - 1] = "T"
    else:  # busy
        for s in snares:
            if intensity >= 2 and pattern[s - 1] is None:
                pattern[s - 1] = "T"
            if s + 2 < steps and pattern[s + 2] is None:
                pattern[s + 2] = "K"
        if intensity >= 3:
            pattern[steps - 1] = "T"

    if intensity == 0:
        pattern = [tok if i % 4 == 0 else None for i, tok in enumerate(pattern)]
    return pattern


@dataclass(frozen=True)
class ScheduledNote:
    """One drum note placed on the beat grid."""

    time_s: float
    note: int
    velocity: int
    source: str     # "groove" or "fill"


class GrooveEngine:
    """Beats in, drum notes out. Pure decision logic, no clocks, no I/O."""

    def __init__(
        self,
        intensity: int = 2,
        mode: str = "groove",
        beats_per_bar: int = 4,
        fill_every_bars: int = 8,
        fill_probability: float = 0.30,
        rng_seed: int | None = None,
        kt_min_gap_s: float = 0.0,
        snare_min_gap_s: float = 0.0,
        grouping: tuple[int, ...] | None = None,
    ) -> None:
        self._beats_per_bar = 0
        self._grouping: tuple[int, ...] = ()
        self.set_meter(beats_per_bar, grouping)
        self._intensity = 0
        self._mode = "groove"
        self.set_intensity(intensity)
        self.set_mode(mode)

        self._fill_every_bars = max(int(fill_every_bars), 1)
        self._fill_probability = min(max(float(fill_probability), 0.0), 1.0)

        self._rng = random.Random(rng_seed)
        self._force_fill_next_bar = False
        self._active_fill_bar: int | None = None

        # Physical floors, taken from the fleet on stage. Kick and tom share
        # one bot (the firmware routes 36 to the tom), so they share a floor;
        # pre-thinning here means a pattern the bot cannot play is never
        # asked for, instead of being asked for and dropped downstream.
        self._kt_min_gap_s = max(float(kt_min_gap_s), 0.0)
        self._snare_min_gap_s = max(float(snare_min_gap_s), 0.0)
        self._last_kt_s: float | None = None
        self._last_snare_s: float | None = None
        self.thinned = 0

    @property
    def intensity(self) -> int:
        return self._intensity

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def beats_per_bar(self) -> int:
        return self._beats_per_bar

    @property
    def grouping(self) -> tuple[int, ...]:
        return self._grouping

    def set_meter(self, beats_per_bar: int, grouping: tuple[int, ...] | None = None) -> None:
        """Change the bar live. A pending fill is forgotten: its bar is gone."""
        if beats_per_bar < 1:
            raise ValueError("beats_per_bar must be at least 1")
        groups = tuple(grouping) if grouping else default_grouping(int(beats_per_bar))
        check_grouping(groups, int(beats_per_bar))
        self._beats_per_bar = int(beats_per_bar)
        self._grouping = groups
        self._active_fill_bar = None

    def set_intensity(self, value: int) -> None:
        self._intensity = min(max(int(value), 0), 4)

    def set_mode(self, value: str) -> None:
        lowered = str(value).strip().lower()
        if lowered not in _MODE_SET:
            raise ValueError(f"unknown mode {value!r}; one of {', '.join(_MODE_SET)}")
        self._mode = lowered

    def request_fill(self) -> None:
        self._force_fill_next_bar = True

    def notes_for_beat(self, beat: BeatEvent, confidence: float) -> list[ScheduledNote]:
        """The notes this beat carries, as absolute times on the beat's clock."""
        confidence = float(confidence)

        if beat.beat_in_bar == 1:
            self._roll_fill_decision(beat.bar_index, confidence)

        use_fill = (
            self._active_fill_bar == beat.bar_index
            and beat.beat_in_bar == self._beats_per_bar
            and confidence >= FILL_CONFIDENCE
        )

        if use_fill:
            tokens = self._fill_tokens()
        else:
            pattern = self._pattern_tokens()
            start = ((beat.beat_in_bar - 1) * 4) % len(pattern)
            tokens = pattern[start:start + 4]

        notes: list[ScheduledNote] = []
        substep_s = beat.period_s / 4.0
        for step, token in enumerate(tokens):
            if token is None:
                continue
            notes.append(ScheduledNote(
                time_s=beat.time_s + step * substep_s,
                note=_NOTE_MAP[token],
                velocity=self._velocity_for(token),
                source="fill" if use_fill else "groove",
            ))
        return self._thin_to_fit(notes)

    def _thin_to_fit(self, notes: list[ScheduledNote]) -> list[ScheduledNote]:
        """Drop notes the shared hardware could never land, earliest wins.

        Within one beat the strong subdivisions come first, so a downbeat
        kick survives and the offbeat crowding it is what goes; across a
        beat boundary it is simply first-come. With today's fleet the floors
        sit well under a sixteenth at any supported tempo, so this is
        insurance for denser patterns, not a daily editor.
        """
        if not self._kt_min_gap_s and not self._snare_min_gap_s:
            return notes
        kept: list[ScheduledNote] = []
        for note in notes:
            if note.note == 38:
                last, gap = self._last_snare_s, self._snare_min_gap_s
            else:
                last, gap = self._last_kt_s, self._kt_min_gap_s
            if last is not None and note.time_s < last - 1.0:
                # The grid jumped backwards (a relock); stale floors are void.
                self._last_kt_s = self._last_snare_s = None
                last = None
            if last is not None and gap and note.time_s - last < gap:
                self.thinned += 1
                continue
            if note.note == 38:
                self._last_snare_s = note.time_s
            else:
                self._last_kt_s = note.time_s
            kept.append(note)
        return kept

    def _roll_fill_decision(self, bar_index: int, confidence: float) -> None:
        if confidence < FILL_CONFIDENCE:
            self._active_fill_bar = None
            self._force_fill_next_bar = False
            return

        should_fill = False
        if self._force_fill_next_bar:
            should_fill = True
            self._force_fill_next_bar = False
        elif bar_index > 0 and (bar_index % self._fill_every_bars) == 0:
            should_fill = self._rng.random() <= self._fill_probability

        self._active_fill_bar = bar_index if should_fill else None

    def _pattern_tokens(self) -> list[str | None]:
        return build_pattern(self._mode, self._intensity, self._grouping)

    def _fill_tokens(self) -> list[str | None]:
        if self._intensity <= 1:
            return ["S", None, "T", "S"]
        if self._intensity == 2:
            return ["S", "T", "S", "T"]
        return ["T", "S", "T", "S"]

    def _velocity_for(self, token: str) -> int:
        velocity_table = {
            "K": (72, 80, 92, 104, 116),
            "S": (78, 88, 98, 110, 120),
            "T": (70, 80, 92, 104, 116),
        }
        return velocity_table[token][self._intensity]
