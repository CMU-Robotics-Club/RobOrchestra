"""What harmony the pianist is in, and when it moves.

Harmony matters to a drummer in three specific ways, and this module is
built around them rather than around transcribing chords for their own
sake. Chord *changes* are where kicks want to land, so the tracker names
the current chord from a decaying pitch-class profile and notices when the
name changes. Changes come at a rhythm — every bar, every two beats — that
can be read from the last few and *predicted*, which matters because the
drums for a beat are committed a fraction of a second before the piano
plays it, and a prediction is the only way to be there on time. And a
dominant resolving to the tonic is a cadence, the strongest marker of a
phrase boundary the piano ever gives, so a key is estimated too (the
Krumhansl-Schmuckler way, over a longer memory) purely to know which chord
is which.

Triads only, major and minor. A seventh chord scores as its triad, a
sus chord as whichever triad it leans to, and that is fine: nobody kicks
differently for a ninth.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import exp, sqrt

NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
MAJOR = (0, 4, 7)
MINOR = (0, 3, 7)

# The chord profile is beat-synchronous: what was played since the last
# beat, plus a fraction of what the profile held before, so a chord that
# changes on a beat is named on that beat, a chord that is merely held
# stays named, and a decaying tail never outvotes the present.
CHORD_CARRY = 0.35
# The key has a long memory and changes its mind reluctantly: a bar on the
# dominant is a bar on the dominant, not a modulation.
KEY_TAU_S = 30.0
KEY_HYSTERESIS = 0.05       # a new key must correlate this much better than the old
BASS_SPLIT = 52
BASS_WEIGHT = 1.5           # a bass note says more about the chord
NON_CHORD_PENALTY = 0.4
MIN_PROFILE_WEIGHT = 0.25   # below this there is no chord to speak of
CHANGE_HYSTERESIS = 1.15    # a new chord must beat the old by this to count

# Krumhansl-Kessler key profiles.
KEY_MAJOR = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
KEY_MINOR = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)

SPACING_CANDIDATES = (1, 2, 3, 4, 6, 8)
# Harmony that moves every beat is comping, or the reader flapping between
# a chord and its relative: not a rhythm a drummer marks. On a real waltz
# the reader alternated Dm and F beat by beat and half of all beats got a
# "the chord is about to change" kick.
MIN_MARKED_SPACING = 2
SPACING_HISTORY = 6
SPACING_MIN_VOTES = 2


@dataclass(frozen=True)
class Chord:
    root: int           # pitch class
    quality: str        # "maj" | "min"
    confidence: float   # how clearly it beat the runner-up, 0..1

    @property
    def name(self) -> str:
        return NAMES[self.root] + ("" if self.quality == "maj" else "m")

    def same(self, other: Chord | None) -> bool:
        return other is not None and self.root == other.root and self.quality == other.quality


@dataclass(frozen=True)
class HarmonyState:
    """The tracker's reading at one beat."""

    chord: Chord | None
    key: tuple[int, str] | None     # (tonic pitch class, "major" | "minor")
    changed: bool                   # the chord changed on this beat
    cadence: bool                   # dominant resolved to tonic on this beat
    spacing: int | None             # beats between chord changes, if regular

    @property
    def key_name(self) -> str:
        if self.key is None:
            return "?"
        tonic, mode = self.key
        return NAMES[tonic] + ("" if mode == "major" else "m")


class HarmonyTracker:
    """Note-ons in; chord, key, changes, cadences and change rhythm out."""

    def __init__(self) -> None:
        self._chord_profile = [0.0] * 12    # as of the last beat
        self._window = [0.0] * 12           # notes since the last beat
        self._key_profile = [0.0] * 12
        self._last_t: float | None = None
        self._current: Chord | None = None
        self._changes: deque[int] = deque(maxlen=SPACING_HISTORY + 1)
        self._spacing: int | None = None
        self._key: tuple[int, str] | None = None

    @property
    def chord(self) -> Chord | None:
        return self._current

    @property
    def key(self) -> tuple[int, str] | None:
        return self._key

    def _decay_key_to(self, t_s: float) -> None:
        if self._last_t is not None and t_s > self._last_t:
            k = exp(-(t_s - self._last_t) / KEY_TAU_S)
            self._key_profile = [p * k for p in self._key_profile]
        self._last_t = max(t_s, self._last_t or t_s)

    def on_note(self, note: int, velocity: int, t_s: float) -> None:
        self._decay_key_to(t_s)
        weight = max(1, min(127, int(velocity))) / 127.0
        if note < BASS_SPLIT:
            weight *= BASS_WEIGHT
        pc = int(note) % 12
        self._window[pc] += weight
        self._key_profile[pc] += weight

    def on_beat(self, beat_index: int, t_s: float) -> HarmonyState:
        """Read the harmony at a beat; call once per beat, in order."""
        self._decay_key_to(t_s)
        played = sum(self._window) > 0.0
        if played:
            self._chord_profile = [CHORD_CARRY * old + new
                                   for old, new in zip(self._chord_profile, self._window)]
        self._window = [0.0] * 12
        scores = self._chord_scores()
        candidate = self._best(scores) if played else None
        changed = False
        cadence = False
        previous = self._current
        if candidate is not None:
            if self._current is None:
                self._current, changed = candidate, True
            elif not candidate.same(self._current):
                incumbent = scores[(self._current.root, self._current.quality)]
                if scores[(candidate.root, candidate.quality)] >= CHANGE_HYSTERESIS * max(incumbent, 1e-9):
                    self._current, changed = candidate, True
        if changed:
            self._changes.append(int(beat_index))
            self._spacing = self._infer_spacing()
        self._key = self._estimate_key()
        if changed and previous is not None and self._key is not None:
            cadence = self._is_cadence(previous, self._current, self._key)
        return HarmonyState(chord=self._current, key=self._key, changed=changed,
                            cadence=cadence, spacing=self._spacing)

    def expects_change(self, beat_index: int) -> bool:
        """Whether the pattern of recent changes puts one on this beat."""
        if self._spacing is None or self._spacing < MIN_MARKED_SPACING or not self._changes:
            return False
        since = int(beat_index) - self._changes[-1]
        return since > 0 and since % self._spacing == 0

    # the estimates

    def _chord_scores(self) -> dict[tuple[int, str], float]:
        p = self._chord_profile
        scores: dict[tuple[int, str], float] = {}
        for root in range(12):
            for quality, tones in (("maj", MAJOR), ("min", MINOR)):
                inside = sum(p[(root + t) % 12] for t in tones)
                outside = sum(p) - inside
                scores[(root, quality)] = inside - NON_CHORD_PENALTY * outside
        return scores

    def _best(self, scores: dict[tuple[int, str], float]) -> Chord | None:
        total = sum(self._chord_profile)
        if total < MIN_PROFILE_WEIGHT:
            return None
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        (root, quality), best = ranked[0]
        second = ranked[1][1]
        confidence = max(0.0, min(1.0, (best - second) / total))
        return Chord(root=root, quality=quality, confidence=confidence)

    def _estimate_key(self) -> tuple[int, str] | None:
        profile = self._key_profile
        if sum(profile) < MIN_PROFILE_WEIGHT:
            return self._key
        scores: dict[tuple[int, str], float] = {}
        for tonic in range(12):
            for mode, template in (("major", KEY_MAJOR), ("minor", KEY_MINOR)):
                rotated = [template[(pc - tonic) % 12] for pc in range(12)]
                scores[(tonic, mode)] = _correlation(profile, rotated)
        best = max(scores, key=lambda k: scores[k])
        if self._key is not None and self._key in scores:
            if scores[best] < scores[self._key] + KEY_HYSTERESIS:
                return self._key
        return best

    @staticmethod
    def _is_cadence(previous: Chord, current: Chord, key: tuple[int, str]) -> bool:
        tonic, mode = key
        dominant = Chord((tonic + 7) % 12, "maj", 0.0)
        home = Chord(tonic, "maj" if mode == "major" else "min", 0.0)
        return previous.same(dominant) and current.same(home)

    def _infer_spacing(self) -> int | None:
        changes = list(self._changes)
        if len(changes) < 3:
            return None
        gaps = [b - a for a, b in zip(changes, changes[1:])]
        votes = {c: sum(1 for g in gaps if g == c) for c in SPACING_CANDIDATES}
        spacing, count = max(votes.items(), key=lambda kv: (kv[1], kv[0]))
        return spacing if count >= SPACING_MIN_VOTES else None


def _correlation(a: list[float], b: list[float]) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = sqrt(sum((x - ma) ** 2 for x in a))
    vb = sqrt(sum((y - mb) ** 2 for y in b))
    if va == 0.0 or vb == 0.0:
        return 0.0
    return cov / (va * vb)
