"""The periodicity-based tempo estimator on the rhythms that break voting."""

import math
import random

import pytest

from tutti.core.tempo import (
    TempoHypothesis,
    candidate_periods,
    evaluate_period,
    rank_periods,
    same_period,
    tempo_prior,
)


def best(onsets, preferred=100.0, lo=70.0, hi=180.0):
    hyps = rank_periods(onsets, lo, hi, preferred)
    assert hyps, "no hypotheses at all"
    return hyps[0]


def clicks(bpm, n, start=0.5, weight=1.0):
    return [(start + k * 60.0 / bpm, weight) for k in range(n)]


def backbeat(bpm, n, start=0.5):
    # sqrt-accent weights the way the tracker feeds them: loud 1, strong 3.
    profile = (2.2, 0.48, 1.6, 0.48)
    return [(start + k * 60.0 / bpm, math.sqrt(profile[k % 4])) for k in range(n)]


# the prior

def test_the_prior_peaks_at_the_preferred_tempo_and_falls_faster_above_it():
    assert tempo_prior(100, 100) == pytest.approx(1.0)
    assert tempo_prior(50, 100) > tempo_prior(200, 100)
    assert tempo_prior(120, 100) < 1.0


# plain pulses

def test_steady_clicks_are_read_exactly():
    top = best(clicks(120, 14))
    assert top.bpm == pytest.approx(120, abs=0.5)
    assert top.support == pytest.approx(1.0)


def test_the_period_is_refined_beyond_the_candidate_grid():
    # Candidates are 1% apart; the fit should land much closer than that.
    top = best(clicks(117.3, 16))
    assert top.bpm == pytest.approx(117.3, abs=0.3)


def test_a_waltz_pulse_is_the_beat_not_the_bar():
    profile = (2.2, 0.48, 0.48)
    onsets = [(0.5 + k * 0.5, math.sqrt(profile[k % 3])) for k in range(18)]
    assert best(onsets).bpm == pytest.approx(120, abs=1)


# the cases interval voting gets wrong

def test_swing_eighths_read_as_the_beat_not_the_long_eighth():
    onsets = []
    for k in range(14):
        t = 0.5 + k * 0.5
        onsets.append((t, math.sqrt(1.2)))
        onsets.append((t + 0.5 * 2 / 3, math.sqrt(0.3)))     # the swung "and"
    hyps = rank_periods(onsets, 70, 180, 100)
    assert hyps[0].bpm == pytest.approx(120, abs=2)
    assert all(not same_period(h.period_s, 60.0 / 180) or h.score < hyps[0].score / 2
               for h in hyps[1:])


def test_eighth_note_comping_at_eighty_is_eighty():
    onsets = []
    for k in range(10):
        t = 0.5 + k * 0.75
        onsets.append((t, math.sqrt(1.5 if k % 2 == 0 else 0.5)))
        onsets.append((t + 0.375, math.sqrt(0.3)))
    assert best(onsets).bpm == pytest.approx(80, abs=1)


def test_a_fast_backbeat_reads_as_half_time_unless_told_otherwise():
    # Quarter comping at 160 is the same pattern as eighths at 80, and the
    # prior decides: half time by default, full tempo with a raised preference.
    assert best(backbeat(160, 20)).bpm == pytest.approx(80, abs=1)
    assert best(backbeat(160, 20), preferred=150).bpm == pytest.approx(160, abs=1)


def test_a_mid_tempo_backbeat_is_not_halved():
    assert best(backbeat(140, 16)).bpm == pytest.approx(140, abs=1)
    assert best(backbeat(120, 16)).bpm == pytest.approx(120, abs=1)


def test_a_chord_every_two_beats_still_reads_as_a_pulse():
    # With the slow reading out of range, the pulse must still be there at
    # the fast one, with enough support to lock on.
    top = best([(0.5 + k * 1.0, 1.0) for k in range(8)], lo=70.0)
    assert top.bpm == pytest.approx(120, abs=1)
    assert top.support >= 0.55
    # In range, the slow reading is simply the honest one.
    assert best([(0.5 + k * 1.0, 1.0) for k in range(8)], lo=50.0).bpm == pytest.approx(60, abs=1)


def test_random_onsets_earn_no_confidence():
    rng = random.Random(123)
    t, onsets = 0.5, []
    for _ in range(30):
        onsets.append((t, 1.0))
        t += rng.uniform(0.20, 1.20)
    assert best(onsets).support < 0.5


# the runners-up

def test_the_runners_up_are_distinct_and_ordered():
    hyps = rank_periods(backbeat(120, 16), 70, 180, 100)
    assert 2 <= len(hyps) <= 3
    for a, b in zip(hyps, hyps[1:]):
        assert a.score >= b.score
        assert not same_period(a.period_s, b.period_s)


def test_an_always_period_is_scored_even_when_no_pair_suggests_it():
    hyps = rank_periods(clicks(120, 10), 70, 180, 100, always=(60.0 / 97.0,))
    assert any(same_period(h.period_s, 60.0 / 97.0) for h in hyps) or len(hyps) == 3


def test_too_few_onsets_is_no_answer():
    assert rank_periods(clicks(120, 3), 70, 180, 100) == []
    assert rank_periods([], 70, 180, 100) == []


# pieces

def test_candidates_come_from_pairs_and_their_subdivisions():
    periods = candidate_periods([0.0, 1.0, 2.0], 0.2, 1.2)
    assert any(abs(p - 1.0) < 0.02 for p in periods)
    assert any(abs(p - 0.5) < 0.02 for p in periods)
    assert any(abs(p - 0.25) < 0.02 for p in periods)
    assert all(0.2 <= p <= 1.2 for p in periods)


def test_evaluate_reports_on_grid_and_occupancy_separately():
    times = [0.5 + k * 0.5 for k in range(8)]
    weights = [1.0] * 8
    beat = evaluate_period(times, weights, 0.5)
    assert beat.on_grid == pytest.approx(1.0) and beat.occupancy == pytest.approx(1.0)
    half = evaluate_period(times, weights, 1.0)      # every other onset is a "subdivision"
    assert half.on_grid == pytest.approx(0.75)       # half credit for those
    assert half.on_grid < beat.on_grid
    double = evaluate_period(times, weights, 0.25)   # every other grid point empty
    assert double.on_grid == pytest.approx(1.0)
    assert double.occupancy == pytest.approx(8 / 15)  # 8 onsets over 15 grid points
    assert isinstance(beat, TempoHypothesis)


def test_straight_eighths_support_the_beat_they_subdivide():
    onsets = [(0.5 + k * 0.25, 1.0) for k in range(24)]   # every eighth at 120
    top = best(onsets)
    assert top.bpm == pytest.approx(120, abs=1)
    assert top.support >= 0.7
