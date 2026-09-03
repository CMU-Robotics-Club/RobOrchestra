"""The listener, fed synthetic note streams on a hand-cranked clock."""

import pytest

from tutti.core.listen import CHANGE_BONUS, Listener


def feed_clusters(listener, spacing_s, count, start=0.0, note=60, velocity=80):
    t = start
    for _ in range(count):
        listener.on_note(note, velocity, t)
        t += spacing_s
    return t - spacing_s     # time of the last cluster


# dynamics

def test_the_absolute_extremes_still_count():
    whisper, hammer = Listener(), Listener()
    t_w = feed_clusters(whisper, 0.5, 20, velocity=20)
    t_h = feed_clusters(hammer, 0.5, 20, velocity=110)
    assert whisper.feel(t_w, 0.5).intensity == 1
    assert hammer.feel(t_h, 0.5).intensity >= 3
    assert hammer.feel(t_h, 0.5).loudness > whisper.feel(t_w, 0.5).loudness


def test_dynamics_are_relative_to_the_player():
    # A gentle player whose velocities never leave the forties: their usual
    # level is the middle, playing softer than usual hushes the drums, and
    # playing harder than usual — still only sixty — swells them.
    listener = Listener()
    t = feed_clusters(listener, 0.5, 40, velocity=44)
    usual = listener.feel(t, 0.5).intensity
    assert usual == 2
    t = feed_clusters(listener, 0.5, 12, start=t + 0.5, velocity=28)
    assert listener.feel(t, 0.5).intensity < usual
    t = feed_clusters(listener, 0.5, 12, start=t + 0.5, velocity=44)
    t = feed_clusters(listener, 0.5, 12, start=t + 0.5, velocity=64)
    assert listener.feel(t, 0.5).intensity >= 3


def test_a_consistently_gentle_player_gets_gentler_drums_than_a_forceful_one():
    gentle, forceful = Listener(), Listener()
    t_g = feed_clusters(gentle, 0.5, 30, velocity=32)
    t_f = feed_clusters(forceful, 0.5, 30, velocity=90)
    assert gentle.feel(t_g, 0.5).intensity < forceful.feel(t_f, 0.5).intensity


def test_a_flurry_reads_as_dense_and_thins_the_drums():
    listener = Listener()
    t = feed_clusters(listener, 0.15, 50)   # 6.7 clusters/s = 3.3 per beat at 120
    feel = listener.feel(t, 0.5)
    assert feel.density > 2.6
    assert feel.mode == "sparse"
    assert feel.intensity <= 2


def test_eighths_and_swing_are_comping_not_a_flurry():
    listener = Listener()
    t = feed_clusters(listener, 0.25, 40)   # straight eighths at 120
    assert listener.feel(t, 0.5).mode == "groove"


def test_sustained_pads_read_as_thin_and_lean_in():
    listener = Listener()
    t = feed_clusters(listener, 2.5, 6)     # one pad chord every 5 beats
    feel = listener.feel(t, 0.5)
    assert feel.density < 0.5
    assert feel.mode == "busy"


def test_mode_does_not_flap_on_the_threshold():
    listener = Listener()
    t = feed_clusters(listener, 0.18, 40)               # ~2.8/beat: sparse mode
    assert listener.feel(t, 0.5).mode == "sparse"
    t = feed_clusters(listener, 0.21, 40, start=t + 0.2)   # ~2.4/beat: in the dead zone
    assert listener.feel(t, 0.5).mode == "sparse"
    t = feed_clusters(listener, 0.30, 40, start=t + 0.3)   # ~1.67/beat: clearly below
    assert listener.feel(t, 0.5).mode == "groove"


# accents

def test_bass_and_velocity_both_raise_the_accent():
    def lone_accent(note, velocity):
        return Listener().on_note(note, velocity, 0.0)

    assert lone_accent(36, 100) > lone_accent(60, 100)
    assert lone_accent(60, 100) > lone_accent(60, 50)
    assert lone_accent(36, 100) > lone_accent(48, 100)   # deeper is stronger


def test_extra_notes_of_a_chord_count_less():
    listener = Listener()
    first = listener.on_note(60, 80, 1.000)
    second = listener.on_note(64, 80, 1.005)
    assert second == pytest.approx(first * 0.25)


def test_a_bass_change_earns_the_change_bonus_once():
    moving, static = Listener(), Listener()
    moving.on_note(36, 100, 0.0)     # C
    static.on_note(41, 100, 0.0)     # F
    changed = moving.on_note(41, 100, 1.0)      # C -> F: harmony moved
    stayed = static.on_note(41, 100, 1.0)       # F -> F: it did not
    assert changed - stayed == pytest.approx(CHANGE_BONUS)
    # And only once per cluster.
    again = moving.on_note(41, 90, 1.01)
    assert again < changed


# phrases

def test_playing_through_never_fades():
    listener = Listener()
    t = feed_clusters(listener, 0.5, 20)
    feel = listener.feel(t + 0.4, 0.5)
    assert feel.velocity_scale == 1.0
    assert not feel.resting
    assert not feel.gap_fill


def test_a_hole_earns_one_fill_then_a_fade_then_rest():
    listener = Listener(beats_per_bar=4)
    t = feed_clusters(listener, 0.5, 20)     # typical gap: one beat

    filled = listener.feel(t + 1.0, 0.5)     # 2 beats of silence: the hole
    assert filled.gap_fill
    assert not listener.feel(t + 1.1, 0.5).gap_fill     # one-shot

    still_playing = listener.feel(t + 1.5, 0.5)   # 3 beats: a long hole, not a stop
    assert still_playing.velocity_scale == 1.0

    fading = listener.feel(t + 2.5, 0.5)     # 5 beats: past fade start
    assert 0.0 < fading.velocity_scale < 1.0

    gone = listener.feel(t + 4.0, 0.5)       # 8 beats: faded out entirely
    assert gone.resting

    # Playing again resets everything at once.
    listener.on_note(60, 80, t + 4.2)
    back = listener.feel(t + 4.3, 0.5)
    assert back.velocity_scale == 1.0
    assert not back.resting


def test_eighth_note_comping_is_not_judged_twice_as_harshly():
    # Eighths at 120: the typical gap is half a beat, but a hole and a stop
    # are still measured in beats — silence of one beat is nothing.
    listener = Listener(beats_per_bar=4)
    t = feed_clusters(listener, 0.25, 40)
    assert listener.feel(t + 0.5, 0.5).velocity_scale == 1.0     # one beat: nothing
    assert not listener.feel(t + 0.5, 0.5).gap_fill
    assert listener.feel(t + 1.0, 0.5).gap_fill                   # two beats: a hole
    assert listener.feel(t + 1.5, 0.5).velocity_scale == 1.0     # three: still waiting
    assert listener.feel(t + 2.5, 0.5).velocity_scale < 1.0      # five: they have stopped


def test_keeping_time_holds_through_a_rest_that_would_otherwise_fade():
    by_ear, knows_it = Listener(), Listener(keep_time=True)
    t_e = feed_clusters(by_ear, 0.5, 20)
    t_k = feed_clusters(knows_it, 0.5, 20)
    assert by_ear.feel(t_e + 2.5, 0.5).velocity_scale < 1.0      # 5 beats: fading
    assert knows_it.feel(t_k + 2.5, 0.5).velocity_scale == 1.0   # still keeping time
    assert knows_it.feel(t_k + 5.0, 0.5).velocity_scale < 1.0    # 10 beats: even they stop


def test_pads_are_a_style_not_a_phrase_ending():
    listener = Listener()
    t = feed_clusters(listener, 2.0, 8)      # a chord every 4 beats, steadily
    mid_gap = listener.feel(t + 1.5, 0.5)    # 3 beats into a normal pad gap
    assert mid_gap.velocity_scale == 1.0
    assert not mid_gap.gap_fill
    assert not mid_gap.resting
