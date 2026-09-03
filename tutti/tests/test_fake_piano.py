"""The fake pianist's pure bar generator. No threads, no clocks."""

import random

from tutti.sources.fake_piano import BASS_ROOT, bar_events


def test_a_bar_is_deterministic_per_seed():
    a = bar_events(0, 10.0, 100.0, 4, random.Random(7))
    b = bar_events(0, 10.0, 100.0, 4, random.Random(7))
    assert a == b
    assert a != bar_events(0, 10.0, 100.0, 4, random.Random(8))


def test_events_sit_near_their_grid_slots():
    period = 60.0 / 100.0
    for seed in range(6):
        for ev in bar_events(0, 10.0, 100.0, 4, random.Random(seed)):
            # Pushes land on half-beats; rolls and jitter smear a chord by at
            # most 12ms + 10ms past its slot.
            offset = (ev.t_s - 10.0) % (period / 2.0)
            distance = min(offset, period / 2.0 - offset)
            assert distance <= 0.022 + 1e-9


def test_the_downbeat_bass_is_the_lowest_and_loudest():
    for seed in range(10):
        events = bar_events(0, 10.0, 100.0, 4, random.Random(seed))
        bass = [e for e in events if e.note == BASS_ROOT]
        assert len(bass) == 1
        assert bass[0].note == min(e.note for e in events)
        assert bass[0].velocity == max(e.velocity for e in events)


def test_a_waltz_bar_ends_at_beat_three():
    period = 60.0 / 120.0
    for seed in range(6):
        for ev in bar_events(0, 0.0, 120.0, 3, random.Random(seed)):
            assert ev.t_s < 3 * period


def test_velocities_are_valid_midi():
    for seed in range(6):
        for ev in bar_events(0, 0.0, 90.0, 4, random.Random(seed)):
            assert 1 <= ev.velocity <= 127
