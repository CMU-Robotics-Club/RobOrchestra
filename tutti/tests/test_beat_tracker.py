"""Beat tracker driven with synthetic onset times: no audio, no wall clock.

The pump helper interleaves on_onset() and advance() exactly the way the jam
tick thread does, on a hand-cranked clock, so every test runs in
milliseconds and is fully deterministic.
"""

import random

import pytest

from tutti.core.beat import BeatTracker


def pump(tracker, onsets, until_s, step=0.01):
    events = []
    pending = sorted(onsets)
    i = 0
    t = 0.0
    while t <= until_s:
        while i < len(pending) and pending[i] <= t:
            tracker.on_onset(pending[i])
            i += 1
        events.extend(tracker.advance(t))
        t += step
    return events


def clicks(bpm, n, start=0.5):
    period = 60.0 / bpm
    return [start + k * period for k in range(n)]


# locking

def test_locks_onto_a_steady_pulse():
    tracker = BeatTracker()
    pump(tracker, clicks(120, 24), until_s=13.0)
    state = tracker.state
    assert state.locked
    assert state.bpm == pytest.approx(120, abs=3)
    assert state.confidence >= 0.55


def test_relocks_after_a_tempo_change():
    tracker = BeatTracker()
    slow = clicks(100, 16)
    fast = [slow[-1] + (k + 1) * 60.0 / 130 for k in range(24)]
    pump(tracker, slow + fast, until_s=fast[-1] + 0.2)
    state = tracker.state
    assert state.locked
    assert state.bpm == pytest.approx(130, abs=6)
    assert state.confidence >= 0.50


def test_random_onsets_never_lock():
    rng = random.Random(123)
    t, onsets = 0.5, []
    for _ in range(30):
        onsets.append(t)
        t += rng.uniform(0.20, 1.20)
    tracker = BeatTracker()
    events = pump(tracker, onsets, until_s=t + 0.5)
    assert not tracker.state.locked
    assert tracker.state.confidence < 0.55
    assert events == []


def test_silence_unlocks_and_stops_the_flywheel():
    tracker = BeatTracker()
    pulse = clicks(120, 24)
    pump(tracker, pulse, until_s=pulse[-1] + 0.1)
    assert tracker.state.locked

    late = pump(tracker, [], until_s=pulse[-1] + 7.0)
    assert not tracker.state.locked
    # Nothing was emitted past the unlock horizon.
    assert all(e.time_s <= pulse[-1] + 5.0 for e in late)
    assert tracker.advance(pulse[-1] + 8.0) == []


# chords and syncopation

def test_a_chord_is_one_onset():
    tracker = BeatTracker()
    assert tracker.on_onset(1.000)
    assert not tracker.on_onset(1.008)
    assert not tracker.on_onset(1.030)
    assert tracker.onsets == 1


def test_rolled_chords_still_lock():
    tracker = BeatTracker()
    onsets = []
    for t in clicks(120, 20):
        onsets += [t, t + 0.006, t + 0.012]     # three-note roll per click
    pump(tracker, onsets, until_s=onsets[-1] + 0.2)
    assert tracker.state.locked
    assert tracker.state.bpm == pytest.approx(120, abs=3)


def test_a_push_does_not_move_the_grid_or_the_beat_count():
    # Every other beat carries a push on the "and". The emitted beats must
    # stay on the clicks, never on the pushes, and the beat count must not
    # slip: click k keeps landing on the same beat index parity throughout.
    period = 60.0 / 120
    onsets = []
    for k, t in enumerate(clicks(120, 40)):
        onsets.append(t)
        if k % 2 == 1:
            onsets.append(t + period / 2)
    tracker = BeatTracker()
    events = pump(tracker, onsets, until_s=onsets[-1] + 0.2)
    click_times = clicks(120, 40)
    for e in events:
        assert any(abs(e.time_s - c) < 0.03 for c in click_times), (
            f"beat emitted at {e.time_s:.3f}, off the clicks")
    # Beat times advance by exactly one period per index: no skips, no doubles.
    for a, b in zip(events, events[1:]):
        assert b.time_s - a.time_s == pytest.approx(period, abs=0.03)


def test_a_grid_locked_onto_the_offbeats_re_acquires():
    period = 60.0 / 120
    before = clicks(120, 20)
    # The pianist shifts by half a beat for good; the old grid is now wrong.
    after = [before[-1] + period / 2 + k * period for k in range(1, 20)]
    tracker = BeatTracker()
    pump(tracker, before, until_s=before[-1] + 0.1)
    events = pump(tracker, after, until_s=after[-1] + 0.1)
    assert events
    late = [e for e in events if e.time_s > after[6]]
    assert late
    for e in late:
        assert any(abs(e.time_s - t) < 0.05 for t in after), (
            f"beat at {e.time_s:.3f} never re-acquired the shifted pulse")


def test_offbeat_eighths_do_not_break_the_lock():
    period = 60.0 / 120
    onsets = []
    for k, t in enumerate(clicks(120, 24)):
        onsets.append(t)
        if k % 4 == 3:
            onsets.append(t + period / 2)   # a push on the "and"
    tracker = BeatTracker()
    pump(tracker, onsets, until_s=onsets[-1] + 0.2)
    assert tracker.state.locked
    assert tracker.state.bpm == pytest.approx(120, abs=5)


# tempo hypotheses

def test_swing_locks_on_the_beat():
    period = 60.0 / 120
    onsets = []
    for t in clicks(120, 24):
        onsets.append((t, 1.2))
        onsets.append((t + period * 2 / 3, 0.3))
    tracker = BeatTracker()
    events = pump_accented(tracker, onsets, until_s=onsets[-1][0] + 0.2)
    assert tracker.state.locked
    assert tracker.state.bpm == pytest.approx(120, abs=2)
    beat_times = clicks(120, 26)     # includes the beat predicted past the last onset
    for e in events:
        assert any(abs(e.time_s - t) < 0.04 for t in beat_times), (
            f"beat at {e.time_s:.3f} is on a swung eighth, not the beat")


def test_eighth_note_comping_locks_at_the_slow_tempo():
    onsets = []
    for k, t in enumerate(clicks(80, 20)):
        onsets.append((t, 1.5 if k % 2 == 0 else 0.5))
        onsets.append((t + 0.375, 0.3))
    tracker = BeatTracker()
    pump_accented(tracker, onsets, until_s=onsets[-1][0] + 0.2)
    assert tracker.state.locked
    assert tracker.state.bpm == pytest.approx(80, abs=2)


def test_an_even_run_of_fast_notes_is_a_pulse():
    # A scale at five notes a second: every onset is a subdivision of any
    # beat, so no beat-level reading scores much on-grid support, yet the
    # run is perfectly regular and a drummer would take it. It must lock,
    # and at a tempo that divides the run evenly.
    onsets = [(0.5 + k * 0.2, 0.6) for k in range(40)]
    tracker = BeatTracker()
    pump_accented(tracker, onsets, until_s=onsets[-1][0] + 0.2)
    assert tracker.state.locked
    ratio = 300.0 / tracker.state.bpm         # notes per beat
    assert abs(ratio - round(ratio)) < 0.05, f"{tracker.state.bpm:.1f} BPM does not divide 300 notes/min"


def test_a_burst_of_odd_onsets_does_not_retune():
    period = 60.0 / 120
    onsets = [(t, 1.0) for t in clicks(120, 40)]
    # Two stray onsets at an unrelated spacing, then the pulse carries on.
    stray_at = onsets[19][0]
    onsets += [(stray_at + 0.21, 1.0), (stray_at + 0.42, 1.0)]
    tracker = BeatTracker()
    pump_accented(tracker, onsets, until_s=onsets[-1][0] + 0.2)
    assert tracker.state.bpm == pytest.approx(120, abs=2)
    assert tracker.state.locked


def test_the_runner_up_tempo_is_visible():
    tracker = BeatTracker()
    onsets = [(t, 1.0) for t in clicks(120, 16)]
    pump_accented(tracker, onsets, until_s=onsets[-1][0] + 0.2)
    state = tracker.state
    assert state.locked
    assert all(abs(alt - 120) > 4 for alt in state.alternatives)


# a declared tempo

def lock_index(tracker, onsets):
    for k, (t, a) in enumerate(onsets):
        tracker.on_onset(t, a)
        tracker.advance(t)
        if tracker.state.locked:
            return k + 1
    return None


def test_a_declared_tempo_comes_in_on_the_count():
    pulse = [(t, 1.0) for t in clicks(72, 16)]
    assert lock_index(BeatTracker(tempo_hint=72), list(pulse)) < lock_index(BeatTracker(), list(pulse))
    assert lock_index(BeatTracker(tempo_hint=72), list(pulse)) == 3     # two gaps at the tempo


def test_a_count_in_needs_gaps_related_to_the_declared_tempo():
    # Three notes at gaps that are nothing to do with 72 are not a count-in.
    tracker = BeatTracker(tempo_hint=72)
    for t in (0.5, 0.81, 1.28):
        tracker.on_onset(t, 1.0)
        tracker.advance(t)
    assert not tracker.state.locked


def test_a_run_at_a_subdivision_of_the_declared_tempo_is_heard_at_that_tempo():
    # Sixteenths at 72: the count-in does not fire (no gap is a beat), but
    # the ranking, with the prior narrowed on 72, reads them as 72 and not
    # as some other grouping of the same notes.
    run = [(0.5 + k * 60.0 / 72 / 4, 0.6) for k in range(24)]
    tracker = BeatTracker(tempo_hint=72)
    pump_accented(tracker, run, until_s=run[-1][0] + 0.2)
    assert tracker.state.locked
    assert tracker.state.bpm == pytest.approx(72, abs=2)


def test_a_declared_tempo_follows_the_player_around_it():
    # Told 72, played at 80: the hint is a prior, not a cage.
    pulse = [(t, 1.0) for t in clicks(80, 20)]
    tracker = BeatTracker(tempo_hint=72)
    pump_accented(tracker, pulse, until_s=pulse[-1][0] + 0.2)
    assert tracker.state.locked
    assert tracker.state.bpm == pytest.approx(80, abs=2)


def test_a_declared_tempo_settles_the_octave():
    # Quarter comping at 160 reads as half time by default; declaring 160
    # makes it 160, and declaring 80 makes it 80. Both are honest.
    profile = (2.2, 0.48, 1.6, 0.48)
    onsets = [(0.5 + k * 60.0 / 160, profile[k % 4]) for k in range(32)]
    fast, slow = BeatTracker(tempo_hint=160), BeatTracker(tempo_hint=80)
    pump_accented(fast, onsets, until_s=onsets[-1][0] + 0.2)
    pump_accented(slow, onsets, until_s=onsets[-1][0] + 0.2)
    assert fast.state.bpm == pytest.approx(160, abs=3)
    assert slow.state.bpm == pytest.approx(80, abs=3)


def test_a_declared_tempo_keeps_time_through_a_rest():
    pulse = clicks(72, 12)
    told = BeatTracker(tempo_hint=72)
    untold = BeatTracker()
    pump(told, pulse, until_s=pulse[-1] + 0.1)
    pump(untold, pulse, until_s=pulse[-1] + 0.1)
    assert told.state.locked and untold.state.locked
    # Six seconds of rest: about seven beats at 72.
    told_events = pump(told, [], until_s=pulse[-1] + 6.0)
    untold_events = pump(untold, [], until_s=pulse[-1] + 6.0)
    assert told.state.locked, "a drummer who knows the tempo plays through a rest"
    assert not untold.state.locked
    assert len(told_events) > len(untold_events)


# rubato

def test_a_ritardando_is_followed_not_steamrolled():
    steady = clicks(120, 16)
    t = steady[-1]
    slowing = []
    period = 60.0 / 120
    for k in range(10):
        period *= 1.03            # each beat 3% longer than the last
        t += period
        slowing.append(t)
    tracker = BeatTracker()
    pump(tracker, steady, until_s=steady[-1] + 0.05)
    events = pump(tracker, slowing, until_s=slowing[-1] + 0.05)
    assert tracker.state.rubato > 1.03
    late = [e for e in events if e.time_s > slowing[4]]
    assert late
    for e in late:
        nearest = min(abs(e.time_s - s) for s in slowing)
        # A sustained 3%-per-beat ritardando is steep; a following drummer
        # lags it a little too. What matters is that the lag stays bounded
        # instead of compounding into a beat of its own.
        assert nearest < 0.075, f"beat at {e.time_s:.3f} is {nearest * 1000:.0f}ms off the slowing pulse"


def test_steady_playing_reports_no_rubato():
    tracker = BeatTracker()
    pulse = clicks(120, 24)
    pump(tracker, pulse, until_s=pulse[-1] + 0.1)
    assert tracker.state.rubato == pytest.approx(1.0, abs=0.02)


# the emitted grid

def test_emitted_beats_are_one_period_apart():
    tracker = BeatTracker()
    pulse = clicks(120, 24)
    events = pump(tracker, pulse, until_s=pulse[-1] + 0.1)
    assert len(events) >= 8
    for a, b in zip(events, events[1:]):
        assert b.time_s - a.time_s == pytest.approx(a.period_s, abs=0.02)


def test_bar_counting_follows_the_declared_meter():
    tracker = BeatTracker(beats_per_bar=3)
    pulse = clicks(120, 24)
    events = pump(tracker, pulse, until_s=pulse[-1] + 0.1)
    assert len(events) >= 6
    for k, event in enumerate(events):
        assert event.beat_in_bar == (k % 3) + 1
        assert event.bar_index == k // 3


# downbeat inference

def pump_accented(tracker, accented_onsets, until_s, step=0.01):
    """Like pump(), but each onset carries an accent weight."""
    events = []
    pending = sorted(accented_onsets)
    i = 0
    t = 0.0
    while t <= until_s:
        while i < len(pending) and pending[i][0] <= t:
            tracker.on_onset(pending[i][0], pending[i][1])
            i += 1
        events.extend(tracker.advance(t))
        t += step
    return events


def test_accents_pull_beat_one_onto_the_accented_phase():
    # Strong accents on every onset with k % 4 == 2. The tracker locks around
    # onset 13 (k % 4 == 0), so its raw counter starts two beats off the
    # accented phase and inference has real work to do.
    period = 60.0 / 120
    onsets = [(0.5 + k * period, 4.0 if k % 4 == 2 else 0.5) for k in range(48)]
    tracker = BeatTracker()
    events = pump_accented(tracker, onsets, until_s=onsets[-1][0] + 0.3)

    accented_times = {t for t, a in onsets if a == 4.0}
    late_downbeats = [e for e in events[-8:] if e.beat_in_bar == 1]
    assert late_downbeats
    for e in late_downbeats:
        assert any(abs(e.time_s - t) < 0.1 for t in accented_times), (
            f"beat 1 at {e.time_s:.2f} is not on an accented onset")
    # The evidence profile agrees: beat 1's bucket dominates.
    profile = tracker.phase_profile
    assert profile[0] == max(profile)


def test_one_loud_hit_does_not_move_the_bar():
    period = 60.0 / 120
    onsets = [(0.5 + k * period, 1.0) for k in range(40)]
    onsets[17] = (onsets[17][0], 8.0)    # a single sforzando off the phase
    tracker = BeatTracker()
    events = pump_accented(tracker, onsets, until_s=onsets[-1][0] + 0.3)
    # Beat numbering never jumps: any rotation would break the cycle.
    for a, b in zip(events, events[1:]):
        assert b.beat_in_bar == (a.beat_in_bar % 4) + 1


def test_inference_can_be_disabled():
    period = 60.0 / 120
    onsets = [(0.5 + k * period, 4.0 if k % 4 == 2 else 0.5) for k in range(48)]
    tracker = BeatTracker(infer_downbeat=False)
    events = pump_accented(tracker, onsets, until_s=onsets[-1][0] + 0.3)
    for a, b in zip(events, events[1:]):
        assert b.beat_in_bar == (a.beat_in_bar % 4) + 1


def test_merged_chord_notes_still_feed_the_accent_bucket():
    period = 60.0 / 120
    tracker = BeatTracker()
    # Lock first with plain clicks.
    for k in range(20):
        tracker.on_onset(0.5 + k * period, 1.0)
        tracker.advance(0.5 + k * period)
    assert tracker.state.locked
    before = sum(tracker._bar_accent)
    t = 0.5 + 20 * period
    tracker.on_onset(t, 1.0)
    tracker.on_onset(t + 0.01, 2.0)      # merged, accent must still land
    tracker.on_onset(t + 0.02, 2.0)      # merged
    assert sum(tracker._bar_accent) == pytest.approx(before + 5.0)


def test_accent_history_is_dense_and_silent_beats_read_as_zero():
    period = 60.0 / 120
    tracker = BeatTracker()
    for k in range(24):
        if k in (20, 21):
            tracker.advance(0.5 + k * period)      # two beats nobody plays
            continue
        tracker.on_onset(0.5 + k * period, 2.0 if k % 4 == 0 else 1.0)
        tracker.advance(0.5 + k * period)
    history = tracker.accent_history(8)
    assert len(history) == 8
    indices = [i for i, _ in history]
    assert indices == list(range(indices[0], indices[0] + 8))
    accents = [a for _, a in history]
    assert accents.count(0.0) >= 2
    assert max(accents) >= 2.0


def test_set_meter_renumbers_from_a_chosen_downbeat():
    period = 60.0 / 120
    tracker = BeatTracker()
    pulse = clicks(120, 20)
    pump(tracker, pulse, until_s=pulse[-1] + 0.1)
    assert tracker.state.locked
    counter = tracker._beat_counter
    tracker.set_meter(3, downbeat_index=counter + 1)
    assert tracker.beats_per_bar == 3
    later = [pulse[-1] + (k + 1) * period for k in range(9)]
    events = pump(tracker, later, until_s=later[-1] + 0.1)
    assert len(events) >= 6
    for k, event in enumerate(events):
        index = counter + k
        expected = ((index - (counter + 1)) % 3) + 1
        assert event.beat_in_bar == expected


def test_advancing_ahead_emits_beats_early_with_true_grid_times():
    tracker = BeatTracker()
    pulse = clicks(120, 24)
    pump(tracker, pulse, until_s=pulse[-1])
    now = pulse[-1]
    ahead = tracker.advance(now + 0.6)
    assert len(ahead) >= 1
    assert all(e.time_s <= now + 0.6 + 1e-6 for e in ahead)
    # The early look did not distort the grid spacing.
    for a, b in zip(ahead, ahead[1:]):
        assert b.time_s - a.time_s == pytest.approx(a.period_s, abs=1e-6)
