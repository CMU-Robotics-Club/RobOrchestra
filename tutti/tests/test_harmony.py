"""The harmony tracker on scripted chords."""

from tutti.core.harmony import HarmonyTracker

BEAT = 0.5


def play(tracker, chord_notes, start_s, beats, beat_index, velocity=80):
    """Strike a chord on each of `beats` consecutive beats; return the last state."""
    state = None
    for k in range(beats):
        t = start_s + k * BEAT
        for note in chord_notes:
            tracker.on_note(note, velocity, t)
        state = tracker.on_beat(beat_index + k, t + 0.02)
    return state, beat_index + beats


def test_a_major_triad_is_named():
    tracker = HarmonyTracker()
    state, _ = play(tracker, (48, 64, 67, 72), 0.5, 4, 0)      # C in the bass, C E G above
    assert state.chord is not None
    assert state.chord.name == "C"
    assert state.chord.confidence > 0.1


def test_a_minor_triad_is_named():
    tracker = HarmonyTracker()
    state, _ = play(tracker, (45, 60, 64, 69), 0.5, 4, 0)      # A minor
    assert state.chord.name == "Am"


def test_a_change_is_noticed_once():
    tracker = HarmonyTracker()
    _, i = play(tracker, (48, 64, 67), 0.5, 4, 0)
    state, _ = play(tracker, (53, 65, 69, 72), 2.5, 1, i)      # to F
    assert state.chord.name == "F"
    assert state.changed
    state, _ = play(tracker, (53, 65, 69, 72), 3.0, 3, i + 1)
    assert not state.changed


def test_the_rhythm_of_changes_is_learned_and_predicted():
    tracker = HarmonyTracker()
    chords = ((48, 64, 67), (53, 65, 69), (55, 62, 67, 71), (48, 64, 67))     # C F G C
    t, i = 0.5, 0
    for chord in chords * 2:
        _, i = play(tracker, chord, t, 4, i)      # every chord held for four beats
        t += 4 * BEAT
    state = tracker.on_beat(i, t)
    assert state.spacing == 4
    assert tracker.expects_change(i + 4 - (i - tracker._changes[-1]))
    assert not tracker.expects_change(tracker._changes[-1] + 1)


def test_the_key_is_found_and_a_cadence_recognised():
    tracker = HarmonyTracker()
    t, i = 0.5, 0
    # Root-position voicings with the root doubled, as a pianist would play
    # a I-IV-V-I in C.
    C, F, G = (48, 60, 64, 67), (53, 60, 65, 69), (55, 62, 67, 71)
    for chord in (C, F, G, C):
        _, i = play(tracker, chord, t, 4, i)
        t += 4 * BEAT
    assert tracker.key == (0, "major")
    _, i = play(tracker, G, t, 2, i)                      # the dominant...
    t += 2 * BEAT
    state, _ = play(tracker, C, t, 1, i)                  # ...resolves
    assert state.changed and state.cadence
    assert state.key_name == "C"


def test_silence_is_no_chord():
    tracker = HarmonyTracker()
    state = tracker.on_beat(0, 1.0)
    assert state.chord is None and not state.changed
    assert not tracker.expects_change(3)


def test_harmony_moving_every_beat_is_not_a_rhythm_to_mark():
    tracker = HarmonyTracker()
    t, i = 0.5, 0
    # A reader flapping between a chord and its relative minor, beat by beat.
    F, Dm = (53, 57, 60, 65), (50, 57, 62, 65)
    for _ in range(6):
        for chord in (F, Dm):
            _, i = play(tracker, chord, t, 1, i)
            t += BEAT
    state = tracker.on_beat(i, t)
    assert state.spacing in (None, 1)
    assert not any(tracker.expects_change(i + k) for k in range(1, 5))
