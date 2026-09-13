"""The old interactive demo's music, made up beat by beat.

Ported from Software/Music Generation/InteractiveDemoCONDUCTING.pde, which
is the sketch that plays along with a conductor: a xylophone melody that
random-walks through a scale, and snare and tom patterns that fire by
probability. The tables are the sketch's own, and the walk is the sketch's
own rule — half the time a weighted pick from the scale, three times in ten
a step up, twice in ten a step down — so it makes the same kind of music the
club has been demonstrating for years. What changed is that it no longer
owns a clock or a MIDI bus: it hands out notes for a step when asked, and
the conductor's clock decides when a step is.

The sketch stepped in eighth notes with a sixteen-step cycle, so one cycle
is two bars of four. A pattern value is the chance the drum plays on that
step before the density slider is added; -1 marks a step that never plays,
however high the slider goes. Numbers are General MIDI here; the sketch's
36 and 37 were what two particular Arduinos happened to listen for.
"""

from __future__ import annotations

import random

from .conduct import Note

STEPS_PER_BEAT = 2
PATTERN_STEPS = 16

XYLO_PATTERN = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
                1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0)
TOM_PATTERN = (1.0, -1.0, 0.0, -1.0, 0.5, -1.0, 0.0, -1.0,
               1.0, -1.0, 0.0, -1.0, 0.5, 0.0, -1.0, 0.0)
SNARE_PATTERN = (0.5, -1.0, 0.0, -1.0, 1.0, -1.0, 0.0, -1.0,
                 0.5, -1.0, 0.0, -1.0, 1.0, -1.0, 0.0, -1.0)

SNARE_NOTE = 38
TOM_NOTE = 45
XYLO_LOW, XYLO_HIGH = 60, 76      # Xylobot's seventeen keys

DEFAULT_DENSITY = {"xylo": 0.55, "snare": 0.70, "tom": 0.45}   # the sketch's slider defaults

# Velocities the sketch never had: a little more on the downbeats, a little
# less between beats, so a kit with dynamics sounds like it has them.
VELOCITY_DOWNBEAT = 112
VELOCITY_BEAT = 100
VELOCITY_OFFBEAT = 88

# name -> (semitone offsets, pick weights). Weights are the sketch's, which
# lean on the root, third and fifth so the walk sounds tonal rather than
# random. Modes that shared a weight row in the sketch share it here.
_COMMON = (1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75)
SCALES: dict[str, tuple[tuple[int, ...], tuple[float, ...]]] = {
    "major": ((0, 2, 4, 5, 7, 9, 11), (1.00, 0.50, 1.00, 0.25, 1.00, 0.70, 0.40)),
    "dorian": ((0, 2, 3, 5, 7, 9, 10), _COMMON),
    "phrygian": ((0, 1, 3, 5, 7, 8, 10), _COMMON),
    "lydian": ((0, 2, 4, 6, 7, 9, 11), _COMMON),
    "mixolydian": ((0, 2, 4, 5, 7, 9, 10), _COMMON),
    "minor": ((0, 2, 3, 5, 7, 8, 10), _COMMON),
    "harmonic_minor": ((0, 2, 3, 5, 7, 8, 11), _COMMON),
    "melodic_minor": ((0, 2, 3, 5, 7, 9, 11), _COMMON),
    "blues": ((0, 3, 5, 6, 7, 10), (1.00, 1.00, 0.75, 1.00, 1.00, 0.75)),
    "bebop": ((0, 2, 4, 5, 7, 9, 10, 11), (1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75, 0.25)),
    "whole_tone": ((0, 2, 4, 6, 8, 10), (1.00, 0.50, 1.00, 0.50, 0.50, 1.00)),
    "pentatonic": ((0, 2, 4, 7, 9), (1.00, 0.75, 1.00, 1.00, 0.75)),
    "minor_pentatonic": ((0, 3, 5, 7, 10), (1.00, 1.00, 0.75, 1.00, 0.75)),
    "chromatic": (tuple(range(12)), (1.00,) + (0.50,) * 11),
    "iwato": ((0, 1, 5, 6, 10), (1.00, 0.75, 0.75, 0.75, 0.75)),
    "pelog": ((0, 1, 3, 6, 7, 8, 10), (1.00, 0.75, 1.00, 0.75, 1.00, 0.75, 0.75)),
}

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
_FLATS = {"DB": 1, "EB": 3, "GB": 6, "AB": 8, "BB": 10}


def parse_tonic(text: str | int) -> int:
    """A key name ('D', 'Eb', 'f#') or a MIDI note number, as a pitch class 0-11."""
    if isinstance(text, int):
        return text % 12
    raw = str(text).strip()
    if raw.lstrip("-").isdigit():
        return int(raw) % 12
    name = raw.upper().replace("♭", "B").replace("♯", "#")
    if name in _FLATS:
        return _FLATS[name]
    if name.endswith("B") and len(name) == 2 and name not in NOTE_NAMES:
        name = name[0]
    try:
        return NOTE_NAMES.index(name)
    except ValueError:
        raise ValueError(f"unknown key {text!r}; try C, F#, Bb or a MIDI note number") from None


def fold_into_range(note: int, lo: int = XYLO_LOW, hi: int = XYLO_HIGH) -> int:
    """Move a note into the xylophone's range by octaves, as its firmware does."""
    while note < lo:
        note += 12
    while note > hi:
        note -= 12
    return note


class Improviser:
    """Notes for one eighth-note step at a time, in the old demo's style."""

    name = "improv"

    def __init__(
        self,
        scale: str = "major",
        tonic: str | int = "C",
        xylo: float = DEFAULT_DENSITY["xylo"],
        snare: float = DEFAULT_DENSITY["snare"],
        tom: float = DEFAULT_DENSITY["tom"],
        harmony: bool = False,
        seed: int | None = None,
    ) -> None:
        self.set_scale(scale)
        self.set_tonic(tonic)
        self._density = {"xylo": 0.0, "snare": 0.0, "tom": 0.0}
        for role, value in (("xylo", xylo), ("snare", snare), ("tom", tom)):
            self.set_density(role, value)
        self.harmony = bool(harmony)
        self._rng = random.Random(seed)
        self.reset()

    # settings, all changeable while playing

    @property
    def scale(self) -> str:
        return self._scale

    def set_scale(self, name: str) -> None:
        key = str(name).strip().lower().replace("-", "_").replace(" ", "_")
        if key not in SCALES:
            raise ValueError(f"unknown scale {name!r}; one of {', '.join(SCALES)}")
        self._scale = key
        self._offsets, weights = SCALES[key]
        total = sum(weights)
        self._probs = tuple(w / total for w in weights)

    @property
    def tonic(self) -> int:
        return self._tonic

    @property
    def key_name(self) -> str:
        return NOTE_NAMES[self._tonic]

    def set_tonic(self, tonic: str | int) -> None:
        self._tonic = parse_tonic(tonic)

    def density(self, role: str) -> float:
        return self._density[role]

    def set_density(self, role: str, value: float) -> None:
        if role not in self._density:
            raise ValueError(f"no density for {role!r}; xylo, snare or tom")
        self._density[role] = max(0.0, min(1.0, float(value)))

    # the program interface the conductor drives

    @property
    def finished(self) -> bool:
        return False        # it plays for as long as someone conducts

    def reset(self) -> None:
        self._step = 0
        self._prev_index = 1        # the sketch's prev_tone_index_1

    @property
    def step(self) -> int:
        return self._step

    def next_beat(self) -> float:
        return self._step / STEPS_PER_BEAT

    def pop_next(self) -> list[Note]:
        notes = self.notes_for_step(self._step)
        self._step += 1
        return notes

    def describe(self) -> str:
        bar = self._step // (STEPS_PER_BEAT * 4) + 1
        return f"bar {bar} {self.key_name} {self._scale}"

    # the music

    def notes_for_step(self, step: int) -> list[Note]:
        """The sketch's playMelody, for one step of its sixteen-step cycle."""
        index = step % PATTERN_STEPS
        on_beat = step % STEPS_PER_BEAT == 0
        downbeat = index % (STEPS_PER_BEAT * 4) == 0
        velocity = VELOCITY_DOWNBEAT if downbeat else VELOCITY_BEAT if on_beat else VELOCITY_OFFBEAT
        notes: list[Note] = []

        if self._plays(SNARE_PATTERN[index], self._density["snare"]):
            notes.append(Note(SNARE_NOTE, velocity))
        if self._plays(TOM_PATTERN[index], self._density["tom"]):
            notes.append(Note(TOM_NOTE, velocity))
        if self._plays(XYLO_PATTERN[index], self._density["xylo"]):
            degree = self._walk()
            notes.append(Note(self._pitch(degree), velocity))
            if self.harmony:
                third = (degree + 2) % len(self._offsets)
                notes.append(Note(self._pitch(third), max(1, velocity - 12)))
            self._prev_index = degree
        return notes

    def _plays(self, pattern_value: float, density: float) -> bool:
        threshold = min(pattern_value + density, 1.0)
        return self._rng.random() <= threshold

    def _walk(self) -> int:
        """Next scale degree: a weighted pick, a step up, or a step down."""
        n = len(self._offsets)
        r = self._rng.random()
        if r < 0.50:
            pick = self._rng.random()
            for i, p in enumerate(self._probs):
                pick -= p
                if pick < 0.0:
                    return i
            return n - 1
        if r < 0.80:
            return (self._prev_index + 1) % n
        return (self._prev_index - 1) % n

    def _pitch(self, degree: int) -> int:
        return fold_into_range(XYLO_LOW + self._tonic + self._offsets[degree])
