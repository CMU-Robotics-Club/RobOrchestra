import pytest

from tutti.core import plan_score
from tutti.core.fleet import DEFAULT_FLEET
from tutti.core.selftest import build_test_score, describe


def snare_fleet():
    return {k: v for k, v in DEFAULT_FLEET.items() if v.role == "snare"}


def test_pattern_has_three_phases_with_gaps_between_them():
    score = build_test_score()
    times = [e.time_s for e in score.events]
    gaps = [b - a for a, b in zip(times, times[1:])]
    # two phase breaks, each the previous phase's gap plus the 1s rest
    assert sorted(gaps)[-2:] == pytest.approx([1.25, 1.8], abs=0.05)
    assert min(gaps) < 0.05


def test_the_ramp_gets_monotonically_faster():
    score = build_test_score(singles=0, steady=0, ramp=10)
    times = [e.time_s for e in score.events]
    gaps = [b - a for a, b in zip(times, times[1:])]
    assert all(b <= a + 1e-9 for a, b in zip(gaps, gaps[1:]))


def test_every_hit_uses_the_requested_note():
    score = build_test_score(note=41)
    assert {e.note for e in score.events} == {41}


def test_the_ramp_outruns_a_real_bot():
    # If it does not, the test tells you nothing about the bot's limit.
    score = build_test_score()
    fleet = snare_fleet()
    plan = plan_score(score, fleet, {1: list(fleet)})
    assert plan.drops, "ramp should exceed what the snare can sustain"


def test_the_early_phases_are_comfortably_inside_the_limit():
    score = build_test_score(ramp=0)
    fleet = snare_fleet()
    plan = plan_score(score, fleet, {1: list(fleet)})
    assert not plan.drops
    assert not plan.nudged


def test_describe_reports_the_claimed_rate():
    score = build_test_score()
    text = "\n".join(describe(score, snare_fleet()))
    assert "19.0 hits/s" in text
    assert "snarebot-01" in text
