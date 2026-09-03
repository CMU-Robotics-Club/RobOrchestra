"""Tempo from how the onsets line up, with a considered opinion about octaves.

Interval voting — the median of recent gaps between onsets — is easy, and it
is how the first version worked, but a pianist walks straight into its two
blind spots. Swing: the long-short eighths of a jazz feel vote for a tempo
that does not exist. Octaves: eighth-note comping at 80 votes for 160, and
folding into a range cannot know which of the two is the beat.

So this module scores candidate periods against the onset pattern itself.
A period earns credit for the share of onsets sitting on its grid — a
period twice the true one strands every other beat off its grid and loses
half — and for how much of its grid the onsets actually visit — a period
half the true one has in-between points nobody plays, and loses too. A
log-Gaussian prior around a preferred tempo settles what is left: eighths
at 80 and quarters at 160 are the same pattern, and only a sense of where
the beat usually lives tells them apart, which is also how people do it.

Weights are the square root of accent: enough that a swung "and" counts for
less than the beat it follows, not so much that the backbeat's loud-soft
alternation impersonates a subdivision.

Several periods come back, best first, so a tracker can keep the runners-up
alive and change its mind only when one of them keeps winning.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, log2, sqrt

WINDOW_S = 6.0              # how far back the pattern is read
MIN_ONSETS = 4
MAX_MULTIPLE = 4            # a pair may be up to this many periods apart
# Phase resolution. ±1 bin either side of the best counts as on-grid, so 32
# bins is a ±4.7% tolerance: comfortably wider than a pianist's timing
# jitter, and narrow enough that a run of random onsets cannot borrow it.
RESIDUE_BINS = 32
CLUSTER_FRACTION = 0.04     # periods this close are the same hypothesis
TOP_HYPOTHESES = 3

# An onset off the grid but on its half or third is a subdivision of the
# pulse — an eighth, a swung eighth — not a contradiction of it, and earns
# part credit. Less than full, so a period twice the true one, which sees
# every other beat as a "subdivision", still loses to the true one.
HALF_GRID_CREDIT = 0.5
THIRD_GRID_CREDIT = 0.35
SUBDIVISION_TOLERANCE = 1.0 / RESIDUE_BINS   # tighter than the grid itself

# The prior is asymmetric on purpose. Eighth-note comping at 80 and quarter
# comping at 160 are the same onset pattern; something has to decide, and
# the two mistakes are not equal. Reading a fast tune at half time gives a
# drummer's perfectly musical half-time feel; reading a ballad at double
# time is jarring. So the prior falls off faster above the preferred tempo
# than below it, and the effective ceiling sits around 150 BPM unless the
# preferred tempo is raised.
PRIOR_WIDTH_UP = 0.6        # octaves, for tempi above preferred
PRIOR_WIDTH_DOWN = 0.9      # octaves, for tempi below


@dataclass(frozen=True)
class TempoHypothesis:
    """One candidate period and how well the onsets support it."""

    period_s: float
    score: float        # support times the tempo prior; what ranks candidates
    support: float      # on-grid share times occupancy, 0..1; what confidence reads
    on_grid: float
    occupancy: float

    @property
    def bpm(self) -> float:
        return 60.0 / self.period_s


def tempo_prior(bpm: float, preferred_bpm: float, width_octaves: float | None = None) -> float:
    """How plausible a tempo is before hearing anything, peaking at preferred_bpm.

    With no width given the prior is the broad, asymmetric one for a tempo
    nobody has declared. A width is what a declared tempo passes: narrow
    and symmetric, because the player has said where the beat is and the
    only question left is how far they are wandering from it.
    """
    octaves = log2(bpm / preferred_bpm)
    if width_octaves is None:
        width_octaves = PRIOR_WIDTH_UP if octaves > 0 else PRIOR_WIDTH_DOWN
    return exp(-(octaves * octaves) / (2.0 * width_octaves * width_octaves))


def same_period(a: float, b: float) -> bool:
    return abs(a - b) <= CLUSTER_FRACTION * max(a, b)


def candidate_periods(times: list[float], min_period: float, max_period: float) -> list[float]:
    """Every period some pair of onsets suggests, deduplicated to 1% steps."""
    bins: set[int] = set()
    for i in range(len(times)):
        for j in range(i + 1, len(times)):
            gap = times[j] - times[i]
            if gap <= 0.0:
                continue
            for k in range(1, MAX_MULTIPLE + 1):
                period = gap / k
                if min_period <= period <= max_period:
                    bins.add(round(log(period) * 100.0))
    return [exp(b / 100.0) for b in sorted(bins)]


def evaluate_period(times: list[float], weights: list[float], period: float,
                    refine: bool = True) -> TempoHypothesis:
    """Score one period against the onsets, without the prior.

    Candidates arrive quantised to 1%, and over a few bars that much drift
    walks the later onsets out of the tolerances, so the fit is redone once
    at the refined period before the score is trusted.
    """
    first = _evaluate_once(times, weights, period)
    if refine and abs(first.period_s - period) > 1e-9:
        return _evaluate_once(times, weights, first.period_s)
    return first


def _evaluate_once(times: list[float], weights: list[float], period: float) -> TempoHypothesis:
    total = sum(weights)
    origin = times[0]
    bins = [0.0] * RESIDUE_BINS
    members: list[list[int]] = [[] for _ in range(RESIDUE_BINS)]
    for i, t in enumerate(times):
        residue = ((t - origin) / period) % 1.0
        b = int(residue * RESIDUE_BINS) % RESIDUE_BINS
        bins[b] += weights[i]
        members[b].append(i)

    def around(b: int) -> float:
        return bins[(b - 1) % RESIDUE_BINS] + bins[b] + bins[(b + 1) % RESIDUE_BINS]

    best = max(range(RESIDUE_BINS), key=around)
    on_idx = sorted(members[(best - 1) % RESIDUE_BINS] + members[best]
                    + members[(best + 1) % RESIDUE_BINS])
    on_set = set(on_idx)
    on_weight = sum(weights[i] for i in on_idx)

    # Part credit for onsets on the pulse's simple subdivisions.
    centre = (best + 0.5) / RESIDUE_BINS
    sub_weight = 0.0
    for i, t in enumerate(times):
        if i in on_set:
            continue
        offset = (((t - origin) / period) - centre) % 1.0
        if abs(offset - 0.5) <= SUBDIVISION_TOLERANCE:
            sub_weight += HALF_GRID_CREDIT * weights[i]
        elif (abs(offset - 1.0 / 3.0) <= SUBDIVISION_TOLERANCE
              or abs(offset - 2.0 / 3.0) <= SUBDIVISION_TOLERANCE):
            sub_weight += THIRD_GRID_CREDIT * weights[i]
    on_grid = (on_weight + sub_weight) / total if total > 0 else 0.0

    # Occupancy and a refined period, from the on-grid onsets alone.
    reference = max(on_idx, key=lambda i: weights[i])
    indices = [round((times[i] - times[reference]) / period) for i in on_idx]
    span = max(indices) - min(indices) + 1
    occupancy = len(set(indices)) / span if span > 0 else 0.0

    refined = period
    if len(on_idx) >= 2:
        k_mean = sum(indices) / len(indices)
        t_mean = sum(times[i] for i in on_idx) / len(on_idx)
        var = sum((k - k_mean) ** 2 for k in indices)
        if var > 0.0:
            cov = sum((k - k_mean) * (times[i] - t_mean) for k, i in zip(indices, on_idx))
            refined = cov / var
            if not (0.5 * period <= refined <= 1.5 * period):
                refined = period

    # Occupancy enters as a square root: it must still sink a subdivision
    # whose in-between points nobody plays, but a chord every two beats is
    # a perfectly good pulse whose slower reading is out of range, and it
    # should not be held below the lock line for it.
    support = on_grid * sqrt(occupancy)
    return TempoHypothesis(period_s=refined, score=support, support=support,
                           on_grid=on_grid, occupancy=occupancy)


def rank_periods(
    onsets: list[tuple[float, float]],
    min_bpm: float,
    max_bpm: float,
    preferred_bpm: float,
    always: tuple[float, ...] = (),
    window_s: float = WINDOW_S,
    prior_width: float | None = None,
) -> list[TempoHypothesis]:
    """The best few periods for these (time, weight) onsets, best first.

    `always` lists periods to score even if no pair suggests them, so an
    active hypothesis is never silently dropped from the comparison.
    `prior_width` narrows the prior around preferred_bpm for a declared tempo.
    """
    if not onsets:
        return []
    latest = onsets[-1][0]
    recent = [(t, w) for t, w in onsets if t >= latest - window_s]
    if len(recent) < MIN_ONSETS:
        return []
    times = [t for t, _ in recent]
    weights = [max(w, 1e-6) for _, w in recent]

    min_period, max_period = 60.0 / max_bpm, 60.0 / min_bpm
    candidates = candidate_periods(times, min_period, max_period)
    for period in always:
        if min_period <= period <= max_period and not any(same_period(period, c) for c in candidates):
            candidates.append(period)
    if not candidates:
        return []

    scored: list[TempoHypothesis] = []
    for period in candidates:
        raw = evaluate_period(times, weights, period)
        if not (min_period <= raw.period_s <= max_period):
            continue
        prior = tempo_prior(raw.bpm, preferred_bpm, prior_width)
        scored.append(TempoHypothesis(
            period_s=raw.period_s, score=raw.support * prior, support=raw.support,
            on_grid=raw.on_grid, occupancy=raw.occupancy))
    scored.sort(key=lambda h: -h.score)

    # One hypothesis per neighbourhood: the best of each cluster of periods.
    kept: list[TempoHypothesis] = []
    for h in scored:
        if any(same_period(h.period_s, k.period_s) for k in kept):
            continue
        kept.append(h)
        if len(kept) == TOP_HYPOTHESES:
            break
    return kept
