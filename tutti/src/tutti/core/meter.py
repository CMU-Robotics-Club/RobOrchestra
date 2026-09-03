"""Which meter is the pianist in? Score the candidates against the accents.

Beats are not equal. In 4/4 the first is strongest and the third is next;
in a waltz only the first stands out; in 5/4 the accent falls where the
groups begin — 1 and 4 for three-plus-two, 1 and 3 for two-plus-three. So
each candidate meter and grouping is a *template* of strong-beat weights,
and the question "what meter is this?" becomes "which template, laid over
the last few bars of accents at which offset, separates strong beats from
weak ones most cleanly?"

The score is (mean accent on template beats minus mean accent on the rest),
in units of the accent spread, so a loud pianist and a quiet one produce
the same number. Judging over a window of a couple of dozen beats keeps one
odd bar from deciding anything, and the caller adds hysteresis on top: the
declared meter is the incumbent and stays until a challenger beats it
clearly and keeps beating it. Two-beat bars are not candidates because a
2/4 template fits every 4/4 song; the difference between them is a fill
schedule, not a backbeat, and the incumbent decides that.

This module only scores; the accent evidence comes from the Listener via
the BeatTracker's per-beat log, and the switch itself is the jam source's
call.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

# Groupings worth considering for each bar length. Order matters only for
# ties, and ties go to the first listed.
CANDIDATE_GROUPINGS: dict[int, tuple[tuple[int, ...], ...]] = {
    3: ((3,),),
    4: ((4,),),
    5: ((3, 2), (2, 3)),
    6: ((3, 3), (2, 2, 2)),
    7: ((4, 3), (3, 4), (2, 2, 3)),
}

MIN_BEATS = 12          # evidence needed before any guess is offered

# Scores this close count as equal and the simpler meter wins. Wide on
# purpose: a waltz fits 6/4-as-3+3 exactly as well as 3/4, and a genuine
# 6/4 only scores a few percent above 3/4 under these templates, so a narrow
# band would let window alignment flip the answer bar to bar.
TIE_FRACTION = 0.10


@dataclass(frozen=True)
class MeterGuess:
    """One candidate: a bar length, how it clumps, and where beat 1 sits."""

    beats_per_bar: int
    grouping: tuple[int, ...]
    downbeat_index: int     # absolute beat index residue that is beat 1
    score: float


def template(grouping: tuple[int, ...]) -> list[float]:
    """Strong-beat weights for one grouping, beat 1 first.

    The bar's first beat is 1.0, every later group start 0.6, and the
    middle of a four-beat group 0.5 alone or 0.4 inside a longer bar — the
    "beat 3 of 4/4" accent.
    """
    weights = [0.0] * sum(grouping)
    pos = 0
    for gi, length in enumerate(grouping):
        weights[pos] = 1.0 if gi == 0 else 0.6
        if length == 4:
            weights[pos + 2] = 0.5 if len(grouping) == 1 else 0.4
        pos += length
    return weights


def score_history(history: list[tuple[int, float]]) -> list[MeterGuess]:
    """Every candidate scored against a run of (beat index, accent), best first."""
    n = len(history)
    if n < MIN_BEATS:
        return []
    accents = [a for _, a in history]
    mean = sum(accents) / n
    spread = sqrt(sum((a - mean) ** 2 for a in accents) / n) + 1e-6

    guesses: list[MeterGuess] = []
    for m, groupings in CANDIDATE_GROUPINGS.items():
        if n < 2 * m:
            continue
        for grouping in groupings:
            weights = template(grouping)
            for phase in range(m):
                strong_sum = strong_weight = 0.0
                weak: list[float] = []
                for index, accent in history:
                    w = weights[(index - phase) % m]
                    if w > 0.0:
                        strong_sum += w * accent
                        strong_weight += w
                    else:
                        weak.append(accent)
                if strong_weight == 0.0 or not weak:
                    continue
                strong_mean = strong_sum / strong_weight
                weak_mean = sum(weak) / len(weak)
                guesses.append(MeterGuess(
                    beats_per_bar=m,
                    grouping=grouping,
                    downbeat_index=phase,
                    score=(strong_mean - weak_mean) / spread,
                ))
    guesses.sort(key=lambda g: (-g.score, g.beats_per_bar))
    return guesses


def best_guess(guesses: list[MeterGuess]) -> MeterGuess | None:
    """The top guess, with near-ties resolved toward the simpler meter.

    A waltz scores identically as 3/4 and as 6/4 in three-plus-three; the
    shorter bar is the honest answer, and the fill schedule can be argued
    about later.
    """
    if not guesses:
        return None
    top = guesses[0]
    floor = top.score - abs(top.score) * TIE_FRACTION
    tied = [g for g in guesses if g.score >= floor]
    return min(tied, key=lambda g: (g.beats_per_bar, len(g.grouping)))


def best_for_meter(
    guesses: list[MeterGuess],
    beats_per_bar: int,
    grouping: tuple[int, ...] | None = None,
) -> MeterGuess | None:
    """The strongest reading of one bar length (and grouping, if given), any phase."""
    own = [g for g in guesses if g.beats_per_bar == beats_per_bar
           and (grouping is None or g.grouping == tuple(grouping))]
    return max(own, key=lambda g: g.score) if own else None
