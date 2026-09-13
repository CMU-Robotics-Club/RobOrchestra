"""The old interactive demo's music, as a program the conductor can drive."""

import pytest

from tutti.core.improv import (
    PATTERN_STEPS,
    SCALES,
    SNARE_NOTE,
    SNARE_PATTERN,
    STEPS_PER_BEAT,
    TOM_NOTE,
    TOM_PATTERN,
    XYLO_HIGH,
    XYLO_LOW,
    Improviser,
    fold_into_range,
    parse_tonic,
)


def test_keys_parse_from_names_and_numbers():
    assert parse_tonic("C") == 0
    assert parse_tonic("f#") == 6
    assert parse_tonic("Bb") == 10
    assert parse_tonic("Eb") == 3
    assert parse_tonic("B") == 11
    assert parse_tonic(67) == 7
    assert parse_tonic("62") == 2
    with pytest.raises(ValueError):
        parse_tonic("H")


def test_notes_fold_into_the_xylophone():
    assert fold_into_range(59) == 71
    assert fold_into_range(77) == 65
    assert fold_into_range(70) == 70


def test_every_scale_has_a_weight_per_degree():
    for name, (offsets, weights) in SCALES.items():
        assert len(offsets) == len(weights), name
        assert all(0 <= o < 12 for o in offsets), name


def test_the_walk_stays_in_the_scale_and_on_the_instrument():
    imp = Improviser(scale="blues", tonic="A", xylo=1.0, snare=0.0, tom=0.0, seed=7)
    pitch_classes = {(9 + o) % 12 for o in SCALES["blues"][0]}
    xylo_notes = []
    for _ in range(64):
        for n in imp.pop_next():
            if n.note >= XYLO_LOW:
                xylo_notes.append(n.note)
    assert len(xylo_notes) == 64            # density 1: every step
    assert all(XYLO_LOW <= n <= XYLO_HIGH for n in xylo_notes)
    assert all(n % 12 in pitch_classes for n in xylo_notes)
    assert len(set(xylo_notes)) > 3         # it moves


def test_patterns_with_no_density_play_only_where_the_table_is_certain():
    imp = Improviser(xylo=0.0, snare=0.0, tom=0.0, seed=1)
    for step in range(PATTERN_STEPS * 2):
        notes = {n.note for n in imp.notes_for_step(step)}
        i = step % PATTERN_STEPS
        if TOM_PATTERN[i] >= 1.0:
            assert TOM_NOTE in notes
        if TOM_PATTERN[i] < 0.0:
            assert TOM_NOTE not in notes
        if SNARE_PATTERN[i] >= 1.0:
            assert SNARE_NOTE in notes
        if SNARE_PATTERN[i] < 0.0:
            assert SNARE_NOTE not in notes


def test_a_never_step_stays_silent_at_full_density():
    imp = Improviser(xylo=0.0, snare=1.0, tom=1.0, seed=2)
    for step in range(PATTERN_STEPS * 4):
        notes = {n.note for n in imp.notes_for_step(step)}
        i = step % PATTERN_STEPS
        if SNARE_PATTERN[i] < 0.0:
            assert SNARE_NOTE not in notes
        else:
            assert SNARE_NOTE in notes
        if TOM_PATTERN[i] < 0.0:
            assert TOM_NOTE not in notes


def test_steps_are_eighths_and_the_program_never_finishes():
    imp = Improviser(seed=0)
    assert imp.next_beat() == 0.0
    imp.pop_next()
    assert imp.next_beat() == 1.0 / STEPS_PER_BEAT
    assert not imp.finished
    imp.reset()
    assert imp.next_beat() == 0.0


def test_the_same_seed_makes_the_same_music():
    a = Improviser(seed=11)
    b = Improviser(seed=11)
    assert [a.pop_next() for _ in range(32)] == [b.pop_next() for _ in range(32)]


def test_harmony_adds_a_third_above():
    imp = Improviser(scale="major", tonic="C", xylo=1.0, snare=0.0, tom=0.0,
                     harmony=True, seed=5)
    notes = [n for n in imp.notes_for_step(0) if n.note >= XYLO_LOW]
    assert len(notes) == 2
    melody, third = notes
    assert third.velocity < melody.velocity
    assert (third.note - melody.note) % 12 in (3, 4, 8, 9)      # a third, maybe folded


def test_settings_change_live_and_reject_nonsense():
    imp = Improviser()
    imp.set_scale("Minor Pentatonic")
    assert imp.scale == "minor_pentatonic"
    imp.set_tonic("G")
    assert imp.key_name == "G"
    imp.set_density("tom", 2.0)
    assert imp.density("tom") == 1.0
    with pytest.raises(ValueError):
        imp.set_scale("klingon")
    with pytest.raises(ValueError):
        imp.set_density("oboe", 0.5)
    assert imp.describe().startswith("bar 1 G minor_pentatonic")


def test_downbeats_are_louder_than_offbeats():
    imp = Improviser(xylo=0.0, snare=0.0, tom=1.0, seed=1)
    down = imp.notes_for_step(0)[0].velocity
    off = None
    for step in range(1, PATTERN_STEPS):
        if step % STEPS_PER_BEAT and TOM_PATTERN[step] >= 0:
            off = imp.notes_for_step(step)[0].velocity
            break
    assert off is not None and down > off
