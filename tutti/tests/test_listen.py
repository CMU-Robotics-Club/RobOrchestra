"""The listener, fed synthetic note streams on a hand-cranked clock."""

import pytest

from tutti.core.listen import CHANGE_BONUS, MAX_DEPTH_BONUS, Listener


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


def test_gain_is_continuous_and_ordered():
    soft, mid, loud = Listener(), Listener(), Listener()
    t_s = feed_clusters(soft, 0.5, 30, velocity=30)
    t_m = feed_clusters(mid, 0.5, 30, velocity=70)
    t_l = feed_clusters(loud, 0.5, 30, velocity=110)
    g = [x.feel(t, 0.5).gain for x, t in ((soft, t_s), (mid, t_m), (loud, t_l))]
    assert g[0] < g[1] < g[2]
    assert 0.45 <= g[0] and g[2] <= 1.3
    # A player at their usual level swelling by a third moves the gain up.
    listener = Listener()
    t = feed_clusters(listener, 0.5, 40, velocity=45)
    usual = listener.feel(t, 0.5).gain
    t = feed_clusters(listener, 0.5, 10, start=t + 0.5, velocity=60)
    assert listener.feel(t, 0.5).gain > usual


def test_activity_rises_with_gain_and_falls_with_a_flurry():
    calm = Listener()
    t = feed_clusters(calm, 0.5, 30, velocity=70)
    steady = calm.feel(t, 0.5).activity
    loud = Listener()
    t = feed_clusters(loud, 0.5, 30, velocity=110)
    assert loud.feel(t, 0.5).activity > steady
    flurry = Listener()
    t = feed_clusters(flurry, 0.15, 60, velocity=70)
    assert flurry.feel(t, 0.5).activity < steady


def test_bar_features_summarise_and_reset():
    listener = Listener()
    listener.on_note(48, 100, 0.0)
    listener.on_note(64, 60, 0.5)
    listener.on_note(67, 60, 0.505)
    bar = listener.bar_features(beats_per_bar=4)
    assert bar.notes == 3
    assert bar.loudness == pytest.approx((100 + 60 + 60) / 3 / 127)
    assert bar.density == pytest.approx(2 / 4)            # two clusters over four beats
    assert bar.register == pytest.approx((48 + 64 + 67) / 3)
    assert bar.pitch_classes[0] > 0 and bar.pitch_classes[4] > 0 and bar.pitch_classes[7] > 0
    assert sum(bar.pitch_classes) == pytest.approx(1.0)
    empty = listener.bar_features(beats_per_bar=4)
    assert empty.notes == 0 and empty.loudness == 0.0 and sum(empty.pitch_classes) == 0.0
    assert list(listener.recent_clusters) == [0.0, 0.5]


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

def comp(listener, t, notes=(60, 64, 67), velocity=80):
    """One comped chord: the register the hands sit in."""
    for i, n in enumerate(notes):
        listener.on_note(n, velocity, t + 0.002 * i)


def test_bass_and_velocity_both_raise_the_accent():
    def accent_after_chords(note, velocity):
        listener = Listener()
        comp(listener, 0.0)
        comp(listener, 0.5)
        return listener.on_note(note, velocity, 1.0)

    assert accent_after_chords(36, 100) > accent_after_chords(60, 100)
    assert accent_after_chords(60, 100) > accent_after_chords(60, 50)
    assert accent_after_chords(36, 100) > accent_after_chords(48, 100)   # deeper is stronger


def test_bass_is_read_against_the_register_the_hands_sit_in():
    # A left hand in F sits at F3 — above any fixed "left hand" line at E3
    # — but four semitones under the close chords it alternates with, and
    # that is what makes it the bass. A chord note at the floor earns no
    # depth at all.
    listener = Listener()
    comp(listener, 0.0, (57, 60))
    comp(listener, 0.3, (57, 60))
    bass = listener.on_note(53, 60, 0.6)
    assert bass > Listener().on_note(53, 60, 0.0)
    comp(listener, 0.9, (57, 60))
    chord_note = listener.on_note(57, 60, 1.2)
    assert chord_note == pytest.approx(Listener().on_note(57, 60, 0.0))


def test_a_root_under_an_open_chord_is_a_bass_note_once_the_chord_is_in():
    listener = Listener()
    vel = 80 / 127
    total = listener.on_note(36, 80, 0.0)
    for i, n in enumerate((60, 64, 67), start=1):
        total += listener.on_note(n, 80, 0.002 * i)
    # Nothing is known until the cluster is complete...
    assert total == pytest.approx(vel * vel * (1.0 + 3 * 0.25))
    assert listener.take_settled_credit() == 0.0
    # ...and then the open root is worth full depth, banked for the caller.
    listener.on_note(60, 80, 0.5)
    assert listener.take_settled_credit() == pytest.approx(MAX_DEPTH_BONUS)
    assert listener.take_settled_credit() == 0.0       # taken once


def test_an_octave_doubling_arriving_first_is_not_a_bass_note():
    # A close C-E-G-C voicing whose top note registers before the inner
    # ones: 48 then 60 look like a root under an open gap for two
    # milliseconds, and must earn nothing for it.
    listener = Listener()
    vel = 80 / 127
    total = sum(listener.on_note(n, 80, 0.002 * i) for i, n in enumerate((48, 60, 52, 55)))
    assert total == pytest.approx(vel * vel * (1.0 + 3 * 0.25))
    listener.on_note(48, 80, 0.7)
    assert listener.take_settled_credit() == 0.0


def test_a_moving_root_under_chords_earns_the_change_bonus_when_settled():
    listener = Listener()
    for t, root in ((0.0, 36), (0.5, 36), (1.0, 41)):
        listener.on_note(root, 80, t)
        for i, n in enumerate((60, 64, 67), start=1):
            listener.on_note(n, 80, t + 0.002 * i)
        listener.take_settled_credit()
    listener.on_note(60, 80, 1.5)
    settled = listener.take_settled_credit()
    assert settled == pytest.approx(MAX_DEPTH_BONUS + CHANGE_BONUS)


def test_the_reference_follows_the_hands_down():
    # Chords an octave lower are a new register, not a bass line: what was
    # deep before is at the floor now.
    listener = Listener()
    comp(listener, 0.0)
    comp(listener, 0.5)
    deep = listener.on_note(48, 80, 1.0)
    comp(listener, 1.5, (48, 52, 55))
    comp(listener, 2.0, (48, 52, 55))
    shallow = listener.on_note(48, 80, 2.5)
    assert shallow < deep


def test_extra_notes_of_a_chord_count_less():
    listener = Listener()
    first = listener.on_note(60, 80, 1.000)
    second = listener.on_note(64, 80, 1.005)
    assert second == pytest.approx(first * 0.25)


def test_a_bass_change_earns_the_change_bonus_once():
    moving, static = Listener(), Listener()
    for listener in (moving, static):
        comp(listener, 0.0)
        comp(listener, 0.5)
    moving.on_note(36, 100, 1.0)     # C
    static.on_note(41, 100, 1.0)     # F
    changed = moving.on_note(41, 100, 2.0)      # C -> F: harmony moved
    stayed = static.on_note(41, 100, 2.0)       # F -> F: it did not
    assert changed - stayed == pytest.approx(CHANGE_BONUS)
    # And only once per cluster.
    again = moving.on_note(41, 90, 2.01)
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

    assert not listener.feel(t + 0.9, 0.5).gap_fill     # under two beats: a hesitation
    filled = listener.feel(t + 1.5, 0.5)     # 3 beats of silence: the hole
    assert filled.gap_fill
    assert not listener.feel(t + 1.6, 0.5).gap_fill     # one-shot

    still_playing = listener.feel(t + 2.0, 0.5)   # 4 beats: a long hole, not a stop
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
    assert not listener.feel(t + 1.0, 0.5).gap_fill               # two beats: a hesitation
    assert listener.feel(t + 1.5, 0.5).gap_fill                   # three beats: a hole
    assert listener.feel(t + 1.6, 0.5).velocity_scale == 1.0     # still waiting
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
