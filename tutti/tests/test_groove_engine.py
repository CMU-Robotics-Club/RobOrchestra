"""Groove engine driven with fabricated BeatEvents, no tracker involved."""

import pytest

from tutti.core.beat import BeatEvent
from tutti.core.groove import (
    GrooveEngine,
    build_pattern,
    default_grouping,
    parse_grouping,
)


def legacy_four_four(mode, intensity):
    """The hand-written 16-step tables the generator replaced, kept as the oracle."""
    pattern = [None] * 16
    if mode == "sparse":
        for step, tok in ((0, "K"), (4, "S"), (8, "K"), (12, "S")):
            pattern[step] = tok
        if intensity >= 3:
            pattern[10] = "K"
    elif mode == "busy":
        for step, tok in ((0, "K"), (3, "T"), (4, "S"), (6, "K"),
                          (8, "K"), (11, "T"), (12, "S"), (14, "K")):
            pattern[step] = tok
        if intensity <= 1:
            pattern[3] = None
            pattern[11] = None
        if intensity >= 3:
            pattern[15] = "T"
    else:
        for step, tok in ((0, "K"), (4, "S"), (8, "K"), (10, "K"), (12, "S")):
            pattern[step] = tok
        if intensity <= 1:
            pattern[10] = None
        if intensity >= 3:
            pattern[15] = "T"
    if intensity == 0:
        for i in range(16):
            if i not in (0, 4, 8, 12):
                pattern[i] = None
    return pattern


def beat(n, bar=0, t=10.0, bpm=120.0):
    return BeatEvent(time_s=t, bpm=bpm, period_s=60.0 / bpm,
                     beat_in_bar=n, bar_index=bar)


def play_bar(engine, bar=0, confidence=0.9, beats_per_bar=4, bpm=120.0, start=10.0):
    period = 60.0 / bpm
    notes = []
    for n in range(1, beats_per_bar + 1):
        notes += engine.notes_for_beat(
            beat(n, bar=bar, t=start + (n - 1) * period, bpm=bpm), confidence)
    return notes


def test_every_note_lands_on_the_sixteenth_grid():
    engine = GrooveEngine(rng_seed=1)
    period = 60.0 / 120.0
    for n in range(1, 5):
        b = beat(n, t=10.0 + (n - 1) * period)
        for note in engine.notes_for_beat(b, confidence=0.9):
            steps = (note.time_s - b.time_s) / (period / 4.0)
            assert steps == pytest.approx(round(steps), abs=1e-6)
            assert 0 <= round(steps) < 4


def test_only_kick_snare_tom_are_ever_asked_for():
    for mode in ("groove", "sparse", "busy"):
        for intensity in range(5):
            engine = GrooveEngine(intensity=intensity, mode=mode, rng_seed=2)
            engine.request_fill()
            for note in play_bar(engine) + play_bar(engine, bar=1):
                assert note.note in (36, 38, 45)
                assert 1 <= note.velocity <= 127


def test_a_forced_fill_takes_over_the_last_beat():
    engine = GrooveEngine(rng_seed=3, fill_probability=0.0)
    engine.request_fill()
    notes = play_bar(engine, bar=1)
    last_beat = [n for n in notes if n.time_s >= 10.0 + 3 * 0.5]
    assert last_beat
    assert all(n.source == "fill" for n in last_beat)
    assert all(n.source == "groove" for n in notes if n not in last_beat)


def test_fills_stay_home_when_confidence_is_low():
    engine = GrooveEngine(rng_seed=4, fill_probability=1.0)
    engine.request_fill()
    notes = play_bar(engine, bar=8, confidence=0.3)
    assert notes
    assert all(n.source == "groove" for n in notes)


def test_three_four_fill_lands_on_beat_three():
    engine = GrooveEngine(beats_per_bar=3, rng_seed=5, fill_probability=0.0)
    engine.request_fill()
    notes = play_bar(engine, bar=1, beats_per_bar=3)
    fill = [n for n in notes if n.source == "fill"]
    assert fill
    assert all(10.0 + 2 * 0.5 <= n.time_s < 10.0 + 3 * 0.5 for n in fill)


def test_same_seed_same_groove():
    bars = []
    for _ in range(2):
        engine = GrooveEngine(rng_seed=42, fill_probability=1.0)
        bars.append([play_bar(engine, bar=b, start=10.0 + b * 2.0) for b in range(10)])
    assert bars[0] == bars[1]


def test_unknown_mode_is_an_error():
    engine = GrooveEngine()
    with pytest.raises(ValueError):
        engine.set_mode("bebop")


# meters and groupings

def test_the_generator_reproduces_the_hand_written_four_four_exactly():
    for mode in ("groove", "sparse", "busy"):
        for intensity in range(5):
            assert build_pattern(mode, intensity, (4,)) == legacy_four_four(mode, intensity), (
                f"{mode} at intensity {intensity} drifted from the tuned table")


def test_a_waltz_has_one_kick_and_a_snare_on_three():
    pattern = build_pattern("groove", 2, (3,))
    assert len(pattern) == 12
    assert pattern[0] == "K" and pattern[8] == "S"
    assert pattern[4] is None            # no backbeat on 2 in 3/4
    assert pattern[6] == "K"             # the pushing kick before the snare


def test_five_four_groupings_place_the_second_kick_differently():
    three_two = build_pattern("sparse", 2, (3, 2))
    two_three = build_pattern("sparse", 2, (2, 3))
    assert len(three_two) == len(two_three) == 20
    assert [i for i, t in enumerate(three_two) if t == "K"] == [0, 12]
    assert [i for i, t in enumerate(three_two) if t == "S"] == [8, 16]
    assert [i for i, t in enumerate(two_three) if t == "K"] == [0, 8]
    assert [i for i, t in enumerate(two_three) if t == "S"] == [4, 16]


def test_seven_four_is_a_full_bar_of_real_tokens():
    pattern = build_pattern("busy", 4, (4, 3))
    assert len(pattern) == 28
    assert set(pattern) <= {"K", "S", "T", None}
    assert pattern[0] == "K" and pattern[16] == "K"    # both group starts


def test_intensity_zero_keeps_only_the_beats_in_any_meter():
    for grouping in ((3,), (3, 2), (4, 3)):
        pattern = build_pattern("busy", 0, grouping)
        assert all(tok is None for i, tok in enumerate(pattern) if i % 4)


def test_groupings_are_checked_against_the_bar():
    assert parse_grouping("3+2", 5) == (3, 2)
    assert parse_grouping(" 2 + 3 ", 5) == (2, 3)
    with pytest.raises(ValueError):
        parse_grouping("3+3", 5)
    with pytest.raises(ValueError):
        parse_grouping("5", 5)          # a five-beat group has no shape
    with pytest.raises(ValueError):
        parse_grouping("three", 3)
    assert default_grouping(5) == (3, 2)
    assert default_grouping(7) == (4, 3)
    assert default_grouping(9) == (4, 4, 1)


def test_set_meter_switches_the_bar_live():
    engine = GrooveEngine(rng_seed=1, fill_probability=0.0)
    assert len(play_bar(engine)) > 0
    engine.set_meter(3)
    assert engine.beats_per_bar == 3 and engine.grouping == (3,)
    engine.request_fill()
    notes = play_bar(engine, bar=1, beats_per_bar=3)
    assert all(n.time_s < 10.0 + 3 * 0.5 for n in notes)
    assert any(n.source == "fill" for n in notes)
    with pytest.raises(ValueError):
        engine.set_meter(5, (4, 2))


# physical floors

def test_a_shared_kick_tom_floor_pre_thins_the_pattern():
    # busy mode at 120 BPM puts kicks 250ms apart at steps 6 and 8; a 300ms
    # shared floor makes the second one physically impossible, so the engine
    # must not ask for it. Snares live on their own bot and are untouched.
    engine = GrooveEngine(mode="busy", intensity=2, rng_seed=1,
                          fill_probability=0.0, kt_min_gap_s=0.3)
    notes = play_bar(engine, bar=0) + play_bar(engine, bar=1, start=12.0)
    assert engine.thinned >= 2
    kicks_and_toms = [n.time_s for n in notes if n.note in (36, 45)]
    for a, b in zip(kicks_and_toms, kicks_and_toms[1:]):
        assert b - a >= 0.3 - 1e-9
    snares = [n for n in notes if n.note == 38]
    assert len(snares) == 4     # steps 4 and 12, both bars, all kept


def test_no_floor_means_no_thinning():
    engine = GrooveEngine(mode="busy", intensity=4, rng_seed=1)
    play_bar(engine)
    assert engine.thinned == 0


def test_the_floor_resets_when_the_grid_jumps_backwards():
    engine = GrooveEngine(mode="sparse", intensity=2, rng_seed=1,
                          fill_probability=0.0, kt_min_gap_s=0.3)
    late = engine.notes_for_beat(beat(1, t=100.0), confidence=0.9)
    assert any(n.note == 36 for n in late)
    # A relock moved the grid far earlier; stale floors must not mute it.
    early = engine.notes_for_beat(beat(1, bar=1, t=2.0), confidence=0.9)
    assert any(n.note == 36 for n in early)
