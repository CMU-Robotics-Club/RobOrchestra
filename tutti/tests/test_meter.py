"""The meter scorer, fed synthetic accent streams shaped like real comping."""

import random

import pytest

from tutti.core.meter import best_for_meter, best_guess, score_history, template

# Per-beat accent profiles the Listener produces for the fake pianist's
# comping: a loud low root on 1, the fifth on 3 where the bar has one, and
# quiet triads elsewhere.
FOUR = [2.2, 0.48, 1.6, 0.48]
WALTZ = [2.2, 0.48, 0.48]
FIVE_TWO_THREE = [2.2, 0.48, 1.6, 0.48, 0.48]
FIVE_THREE_TWO = [2.2, 0.48, 0.48, 1.6, 0.48]


def stream(profile, bars, offset=0, noise=0.0, seed=0):
    rng = random.Random(seed)
    m = len(profile)
    return [(i, profile[(i - offset) % m] + rng.gauss(0.0, noise))
            for i in range(bars * m)]


def test_templates_have_the_expected_shape():
    assert template((4,)) == [1.0, 0.0, 0.5, 0.0]
    assert template((3,)) == [1.0, 0.0, 0.0]
    assert template((3, 2)) == [1.0, 0.0, 0.0, 0.6, 0.0]
    assert template((4, 3)) == [1.0, 0.0, 0.4, 0.0, 0.6, 0.0, 0.0]


def test_four_four_comping_reads_as_four_four_on_the_downbeat():
    best = best_guess(score_history(stream(FOUR, 6)))
    assert best.beats_per_bar == 4
    assert best.downbeat_index == 0


def test_the_downbeat_offset_is_recovered():
    best = best_guess(score_history(stream(FOUR, 6, offset=2)))
    assert best.beats_per_bar == 4
    assert best.downbeat_index == 2


def test_a_waltz_reads_as_three_not_six():
    best = best_guess(score_history(stream(WALTZ, 8)))
    assert best.beats_per_bar == 3
    assert best.downbeat_index == 0


def test_five_four_comes_with_its_grouping():
    best = best_guess(score_history(stream(FIVE_TWO_THREE, 6)))
    assert (best.beats_per_bar, best.grouping) == (5, (2, 3))
    best = best_guess(score_history(stream(FIVE_THREE_TWO, 6)))
    assert (best.beats_per_bar, best.grouping) == (5, (3, 2))


def test_noise_does_not_change_the_answer():
    for seed in range(5):
        best = best_guess(score_history(stream(FOUR, 8, offset=1, noise=0.25, seed=seed)))
        assert best.beats_per_bar == 4
        assert best.downbeat_index == 1
        best = best_guess(score_history(stream(WALTZ, 10, noise=0.25, seed=seed)))
        assert best.beats_per_bar == 3


def test_flat_playing_gives_no_confident_answer():
    best = best_guess(score_history(stream([1.0, 1.0, 1.0, 1.0], 8)))
    assert best is not None
    assert best.score < 0.5


def test_too_little_evidence_is_no_answer():
    assert score_history(stream(FOUR, 2)[:8]) == []
    assert best_guess([]) is None


def test_the_incumbent_can_be_asked_for_its_own_best_reading():
    guesses = score_history(stream(WALTZ, 8))
    four = best_for_meter(guesses, 4)
    three = best_for_meter(guesses, 3)
    assert three.score > four.score
    assert best_for_meter(guesses, 5, (3, 2)).grouping == (3, 2)
    assert best_for_meter(guesses, 11) is None


def test_scores_are_scale_free():
    loud = best_guess(score_history(stream([x * 3 for x in FOUR], 6)))
    quiet = best_guess(score_history(stream(FOUR, 6)))
    assert loud.score == pytest.approx(quiet.score, rel=1e-6)
