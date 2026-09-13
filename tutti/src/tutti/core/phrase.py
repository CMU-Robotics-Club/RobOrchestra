"""Where in the piece we are: bars into a phrase, phrases into a section.

A drummer plays bar four of a phrase differently from bar one — a fill, a
push into the next phrase — and plays the first bar of a new section
differently again, and knows both without a chart, from the music. This
module keeps that count.

Phrases are counted in bars from the start of the current section, four to
a phrase and two phrases to a period, which covers most popular music and
is wrong in an unsurprising way for the rest. Sections are found by
novelty: each completed bar is summarised (how loud, how busy, how high,
which pitch classes) and compared with what the section has been doing so
far. A change that holds for a whole phrase means the piece has moved on;
an extreme single bar — a sudden fortissimo, a drop to nothing — is enough
on its own. The phrase-length test is what keeps a chord change from
looking like a section: one bar on a new chord sits far from the section's
harmony, but four bars taken together cover the same vocabulary, and only
loudness, density and register are allowed to make a single bar extreme.
A rest bar is neither evidence for nor against anything.

The costs of being wrong are asymmetric — a missed section merely means a
missed accent, a false one means a fill and a downbeat crash in the middle
of a verse — so the thresholds lean towards missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt

from .listen import BarFeatures

BARS_PER_PHRASE = 4
MIN_SECTION_BARS = 4        # a section this young cannot end yet
NOVELTY_THRESHOLD = 1.0
NOVELTY_EXTREME = 3.0       # a single bar this far out is a section by itself
NOVELTY_BARS = BARS_PER_PHRASE      # otherwise, the change must hold this long
SECTION_MEAN_BARS = 16      # the section's own profile remembers this many bars
SECTION_MEAN_ALPHA = 0.3    # and no single bar of it counts for more than this

# One unit of novelty in each feature. Two features moving by a unit at
# once, or one moving by 1.4, crosses the threshold. Loudness is relative
# to the section's own level, because a pianist's louder is louder for
# them; register is an octave, because the bar's mean note wanders half
# that with the melody; and harmony is scaled to a modulation, because a
# four-bar chord is not a new section, however far its triad sits from the
# section's blend.
LOUDNESS_FRACTION = 0.2     # of the section's mean velocity
DENSITY_LOG_UNIT = 0.6      # natural log of the density ratio: about 1.8x
REGISTER_UNIT = 12.0        # semitones
HARMONY_UNIT = 1.0          # cosine distance between pitch-class profiles


@dataclass(frozen=True)
class PhraseContext:
    """Where the bar about to start sits in the piece."""

    bar_in_phrase: int          # 0-based
    bars_per_phrase: int
    phrase_end: bool            # this bar closes a phrase
    hyper_end: bool             # this bar closes a two-phrase period
    section: int                # 0-based section count
    section_started: bool       # this bar opens a new section
    bars_in_section: int        # bars completed in the section so far


def novelty(features: BarFeatures, mean: BarFeatures, harmony: bool = True) -> float:
    """How far a bar, or a run of bars summarised as one, sits from the section."""
    terms = [
        abs(features.loudness - mean.loudness) / (LOUDNESS_FRACTION * max(mean.loudness, 0.1)),
        abs(log(max(features.density, 0.1) / max(mean.density, 0.1))) / DENSITY_LOG_UNIT,
        abs(features.register - mean.register) / REGISTER_UNIT,
    ]
    if harmony:
        terms.append(_cosine_distance(features.pitch_classes, mean.pitch_classes) / HARMONY_UNIT)
    return sqrt(sum(t * t for t in terms) / 2.0)


def summarise(bars: list[BarFeatures]) -> BarFeatures:
    """Several bars as one: means of the levels, the union of the harmony."""
    n = len(bars)
    return BarFeatures(
        loudness=sum(b.loudness for b in bars) / n,
        density=sum(b.density for b in bars) / n,
        register=sum(b.register for b in bars) / n,
        pitch_classes=tuple(sum(b.pitch_classes[i] for b in bars) / n for i in range(12)),
        notes=sum(b.notes for b in bars),
    )


def _cosine_distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sqrt(sum(x * x for x in a))
    nb = sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return 1.0 - dot / (na * nb)


def _blend(mean: BarFeatures, features: BarFeatures, alpha: float) -> BarFeatures:
    return BarFeatures(
        loudness=mean.loudness + alpha * (features.loudness - mean.loudness),
        density=mean.density + alpha * (features.density - mean.density),
        register=mean.register + alpha * (features.register - mean.register),
        pitch_classes=tuple(m + alpha * (f - m)
                            for m, f in zip(mean.pitch_classes, features.pitch_classes)),
        notes=features.notes,
    )


class PhraseTracker:
    """Bar summaries in, phrase and section context out."""

    def __init__(self, bars_per_phrase: int = BARS_PER_PHRASE,
                 min_section_bars: int = MIN_SECTION_BARS) -> None:
        self._bars_per_phrase = max(1, int(bars_per_phrase))
        self._min_section_bars = max(1, int(min_section_bars))
        self._section = 0
        self._bars_in_section = 0
        self._mean: BarFeatures | None = None
        self._mean_bars = 0
        self._recent: list[BarFeatures] = []    # the last few bars, not yet in the mean
        self._section_started = False
        self.bars = 0
        self.section_starts: list[int] = []     # bar counts at which sections began

    @property
    def section(self) -> int:
        return self._section

    def on_bar(self, features: BarFeatures) -> PhraseContext:
        """Take in the bar just completed; return the context for the next."""
        self.bars += 1
        self._section_started = False
        if features.notes == 0:
            # A rest breaks the block; what came before it was this section.
            for bar in self._recent:
                self._absorb(bar)
            self._recent = []
            self._bars_in_section += 1
            return self.context()
        self._recent.append(features)
        if len(self._recent) > NOVELTY_BARS:
            self._absorb(self._recent.pop(0))
        if self._mean is not None and self._bars_in_section >= self._min_section_bars:
            if novelty(features, self._mean, harmony=False) >= NOVELTY_EXTREME:
                self._recent = [features]
                self._begin_section()
                return self.context()
            if (len(self._recent) == NOVELTY_BARS
                    and novelty(summarise(self._recent), self._mean) >= NOVELTY_THRESHOLD):
                self._begin_section()
                return self.context()
        self._bars_in_section += 1
        return self.context()

    def _absorb(self, features: BarFeatures) -> None:
        if self._mean is None:
            self._mean, self._mean_bars = features, 1
            return
        self._mean_bars = min(self._mean_bars + 1, SECTION_MEAN_BARS)
        self._mean = _blend(self._mean, features, min(1.0 / self._mean_bars, SECTION_MEAN_ALPHA))

    def _begin_section(self) -> None:
        bars = self._recent
        self._mean, self._mean_bars = summarise(bars), len(bars)
        self._section += 1
        self._bars_in_section = len(bars)
        self._recent = []
        self._section_started = True
        self.section_starts.append(self.bars - len(bars))

    def context(self) -> PhraseContext:
        bar = self._bars_in_section % self._bars_per_phrase
        period = 2 * self._bars_per_phrase
        return PhraseContext(
            bar_in_phrase=bar,
            bars_per_phrase=self._bars_per_phrase,
            phrase_end=(bar == self._bars_per_phrase - 1),
            hyper_end=(self._bars_in_section % period == period - 1),
            section=self._section,
            section_started=self._section_started,
            bars_in_section=self._bars_in_section,
        )
