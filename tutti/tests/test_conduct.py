"""Conducting: the clock, the score program, and the source that drives them.

Every time here is on a fake clock the tests advance by hand, so a whole
conducted piece runs in milliseconds and every hit's moment can be checked
to the microsecond.
"""

import pytest

from tutti.core import ActuatorModel, Instrument, NoteEvent, Score
from tutti.core.conduct import (
    BOUNCE_RATIO,
    ConductorClock,
    Note,
    ScoreProgram,
    auto_offset_beats,
)
from tutti.core.ensemble import Ensemble
from tutti.sources.conduct import LATE_SKIP_S, RESTART_GAP_S, ConductSource, MetronomeInput
from tutti.transports.loopback import NullTransport


# the clock


def strokes(clock, times, strength=0.7):
    return [clock.on_stroke(t, strength) for t in times]


def test_nothing_is_predicted_before_one_interval_sets_a_tempo():
    c = ConductorClock(count_in=4)
    assert c.time_of_beat(0) is None
    c.on_stroke(1.0)
    assert not c.started
    assert c.time_of_beat(-3) is None


def test_count_in_numbers_beats_so_the_piece_starts_after_it():
    c = ConductorClock(count_in=4)
    kinds = [s.kind for s in strokes(c, [1.0, 1.5, 2.0, 2.5])]
    assert kinds == ["count_in"] * 4
    assert c.bpm == pytest.approx(120.0)
    assert c.anchor_beat == -1
    assert c.time_of_beat(0) == pytest.approx(3.0)        # the stroke after the count-in
    assert c.time_of_beat(0.5) is None                    # the "and" waits for beat 0's stroke
    c.on_stroke(3.0)
    assert c.time_of_beat(0.5) == pytest.approx(3.25)
    assert c.time_of_beat(1) == pytest.approx(3.5)
    assert c.time_of_beat(1.5) is None


def test_a_pickup_falls_inside_the_count_in():
    c = ConductorClock(count_in=4)
    strokes(c, [1.0, 1.5, 2.0])
    assert c.anchor_beat == -2
    assert c.time_of_beat(-1) == pytest.approx(2.5)       # plays on the fourth count-in stroke
    assert c.time_of_beat(-0.5) is None


def test_the_orchestra_holds_one_beat_past_the_last_stroke():
    c = ConductorClock(count_in=2)
    strokes(c, [0.0, 0.5, 1.0, 1.5])                      # beats -2 -1 0 1
    assert c.anchor_beat == 1
    assert c.time_of_beat(2) == pytest.approx(2.0)
    assert c.time_of_beat(2.25) is None
    assert not c.holding(2.0)
    assert c.holding(2.4)


def test_coast_lets_it_run_further_before_holding():
    c = ConductorClock(count_in=2, coast_beats=2)
    strokes(c, [0.0, 0.5, 1.0])                           # anchor beat 0 at 1.0
    assert c.time_of_beat(3) == pytest.approx(2.5)
    assert c.time_of_beat(3.5) is None


def test_a_bounce_is_ignored_and_does_not_move_the_grid():
    c = ConductorClock(count_in=2)
    strokes(c, [0.0, 0.5, 1.0])
    bounce = c.on_stroke(1.0 + 0.5 * BOUNCE_RATIO * 0.9)
    assert bounce.kind == "bounce"
    assert c.bounces == 1
    assert c.anchor_beat == 0
    assert c.time_of_beat(1) == pytest.approx(1.5)
    nxt = c.on_stroke(1.5)
    assert nxt.kind == "beat" and nxt.beat == 1


def test_a_missed_stroke_jumps_the_count_rather_than_falling_behind():
    c = ConductorClock(count_in=2)
    strokes(c, [0.0, 0.5, 1.0])                           # anchor beat 0 at 1.0
    missed = c.on_stroke(2.0)                             # two periods: one was missed
    assert missed.kind == "missed"
    assert missed.beat == 2
    assert c.period_s == pytest.approx(0.5)               # not read as a slow beat


def test_a_long_gap_is_a_fermata_and_the_next_stroke_releases_it():
    c = ConductorClock(count_in=2)
    strokes(c, [0.0, 0.5, 1.0])
    resume = c.on_stroke(4.0)
    assert resume.kind == "resume"
    assert resume.beat == 1
    assert c.period_s == pytest.approx(0.5)
    assert c.time_of_beat(2) == pytest.approx(4.5)


def test_resume_after_coasting_continues_from_where_it_stopped():
    c = ConductorClock(count_in=2, coast_beats=1)
    strokes(c, [0.0, 0.5, 1.0])                           # played through beat 2
    resume = c.on_stroke(4.0)
    assert resume.beat == 2


def test_the_tempo_follows_an_accelerando_with_inertia():
    c = ConductorClock(count_in=2)
    strokes(c, [0.0, 0.6, 1.2])
    assert c.period_s == pytest.approx(0.6)
    c.on_stroke(1.7)                                      # a 0.5 gap
    assert 0.5 < c.period_s < 0.6                         # moved toward it, not onto it
    for t in (2.2, 2.7, 3.2, 3.7, 4.2):
        c.on_stroke(t)
    assert c.period_s == pytest.approx(0.5, abs=0.02)


def test_phase_takes_most_of_a_late_stroke():
    c = ConductorClock(count_in=2, period_alpha=0.0)      # tempo pinned, phase free
    strokes(c, [0.0, 0.5, 1.0])
    c.on_stroke(1.6)                                      # 100 ms late
    predicted = c.time_of_beat(2)
    assert 2.0 < predicted <= 2.1
    assert predicted == pytest.approx(1.5 + 0.7 * 0.1 + 0.5)


def test_two_strokes_too_far_apart_start_the_count_in_over():
    c = ConductorClock(count_in=2, max_period_s=2.0)
    c.on_stroke(0.0)
    again = c.on_stroke(5.0)
    assert again.kind == "restart"
    assert not c.started
    c.on_stroke(5.5)
    assert c.time_of_beat(0) == pytest.approx(6.0)


def test_dynamics_follow_the_size_of_the_strokes():
    c = ConductorClock(count_in=2)
    strokes(c, [0.0, 0.5, 1.0], strength=1.0)
    loud = c.dynamics
    strokes(c, [1.5, 2.0, 2.5, 3.0], strength=0.1)
    assert c.dynamics < loud
    assert c.dynamics < 0.3


def test_out_of_range_tempi_are_clamped():
    c = ConductorClock(count_in=2, min_period_s=0.25, max_period_s=2.0)
    strokes(c, [0.0, 0.3, 0.6, 0.9])
    assert c.period_s == pytest.approx(0.3)
    c.on_stroke(1.02)                                     # 0.12 after: a bounce, ignored
    assert c.last.kind == "bounce"
    for t in (1.1, 1.3, 1.5, 1.7, 1.9, 2.1):              # 300 BPM is off the range
        c.on_stroke(t)
    assert c.period_s == pytest.approx(0.25)


def test_count_in_needs_two_strokes():
    with pytest.raises(ValueError):
        ConductorClock(count_in=1)


# where beat 0 goes


def test_a_piece_starting_on_a_downbeat_starts_at_beat_zero():
    assert auto_offset_beats(0.0, 4) == 0.0
    assert auto_offset_beats(8.0, 4) == -8.0


def test_a_pickup_lands_before_beat_zero():
    # Route1: the melody enters on beat 3 of a bar, one beat before the bar line
    assert auto_offset_beats(3.0, 4) == -4.0
    assert auto_offset_beats(1.5, 4) == -4.0
    assert auto_offset_beats(6.0, 3) == -6.0
    assert auto_offset_beats(7.0, 3) == -9.0


# the score program


def ev(beat, note=60, velocity=100, part=1):
    return NoteEvent(part_id=part, note=note, velocity=velocity, time_s=beat * 0.5, beat=beat)


def test_score_program_groups_notes_by_beat_in_order():
    score = Score("t", events=[ev(1.0, 62), ev(0.0, 60), ev(0.0, 38), ev(0.5, 64)])
    p = ScoreProgram(score, offset_beats=0.0)
    assert p.notes == 4
    assert p.next_beat() == 0.0
    assert {n.note for n in p.pop_next()} == {60, 38}
    assert p.next_beat() == 0.5
    assert p.pop_next() == [Note(64, 100)]
    assert p.pop_next() == [Note(62, 100)]
    assert p.finished
    assert p.next_beat() is None and p.pop_next() == []
    p.reset()
    assert p.next_beat() == 0.0


def test_score_program_places_a_pickup_before_beat_zero_by_default():
    score = Score("t", events=[ev(3.0), ev(4.0), ev(5.0)])
    p = ScoreProgram(score, beats_per_bar=4)
    assert p.offset_beats == -4.0
    assert p.first_beat == -1.0
    assert p.describe().startswith("pickup")
    p.pop_next()
    assert p.describe() == "bar 1/1"


def test_score_program_beat_unit_and_offset():
    score = Score("t", events=[ev(0.0), ev(2.0), ev(4.0)])
    p = ScoreProgram(score, beat_unit=2.0, offset_beats=1.0)
    assert [p.next_beat() or p.pop_next() for _ in range(1)] == [1.0]
    assert p.next_beat() == 1.0
    p.pop_next()
    assert p.next_beat() == 2.0


def test_score_program_skips_notes_nothing_on_stage_plays():
    score = Score("t", events=[ev(0.0, 60), ev(0.0, 38), ev(1.0, 90)])
    p = ScoreProgram(score, offset_beats=0.0, accepts={60, 38})
    assert p.notes == 2
    assert p.unplayable == 1


def test_score_program_rejects_bad_arguments():
    with pytest.raises(ValueError):
        ScoreProgram(Score("t"), beat_unit=0)
    with pytest.raises(ValueError):
        ScoreProgram(Score("t"), beats_per_bar=0)


# the source, driven by hand


def fleet():
    return {
        "snarebot": Instrument("snarebot", "snare", ActuatorModel(
            voices=2, cycle_ms=105.0, accepts=frozenset({38}))),
        "xylobot": Instrument("xylobot", "xylo", ActuatorModel(
            voices=17, cycle_ms=55.0, accepts=frozenset(range(60, 77)),
            voice_mode="keyed", lowest_note=60)),
    }


class Harness:
    """A conduct source on a clock the test moves, with beats fed at chosen times."""

    def __init__(self, program, count_in=4, **kw):
        self.now = [0.0]
        self.transport = NullTransport()
        self.ensemble = Ensemble(fleet(), self.transport, clock=lambda: self.now[0])
        self.source = ConductSource(program, count_in=count_in, camera=False, **kw)
        self.source.bind(self.ensemble)

    def run(self, until, beats=(), strength=0.7, step=0.005):
        """Advance to `until`, delivering each beat time in `beats` as it comes."""
        pending = sorted(beats)
        while self.now[0] < until - 1e-9:
            self.now[0] = min(until, self.now[0] + step)
            while pending and pending[0] <= self.now[0] + 1e-9:
                self.source.on_stroke(pending.pop(0), strength)
            self.source._tick(self.now[0])

    @property
    def played(self):
        return [(round(h.play_at_s, 4), h.note) for h in self.transport.received]


def simple_score():
    return Score("t", events=[ev(0.0, 60), ev(0.5, 62), ev(1.0, 64), ev(2.0, 65),
                              ev(2.5, 38), ev(3.0, 67)])


def test_the_piece_starts_on_the_stroke_after_the_count_in():
    h = Harness(ScoreProgram(simple_score(), offset_beats=0.0))
    h.run(3.5, beats=[1.0, 1.5, 2.0, 2.5, 3.0])
    assert h.played[:3] == [(3.0, 60), (3.25, 62), (3.5, 64)]


def test_it_holds_on_the_next_beat_when_the_conductor_stops():
    h = Harness(ScoreProgram(simple_score(), offset_beats=0.0))
    h.run(3.4, beats=[1.0, 1.5, 2.0, 2.5, 3.0])           # anchor beat 0 at 3.0
    h.run(5.0)                                            # no more strokes
    # beat 1 (the next beat) was predicted and played; beat 2 waited
    assert h.played == [(3.0, 60), (3.25, 62), (3.5, 64)]
    assert h.source.clock.holding(5.0)


def test_the_next_stroke_releases_the_hold_at_the_old_tempo():
    h = Harness(ScoreProgram(simple_score(), offset_beats=0.0))
    h.run(3.4, beats=[1.0, 1.5, 2.0, 2.5, 3.0])
    h.run(6.6, beats=[6.0])                               # beat 1 released at 6.0
    assert h.source.last_stroke.kind == "resume"
    assert h.played[-1] == (6.5, 65)                      # beat 2, a period later
    h.run(6.8, beats=[6.5])
    assert h.played[-1] == (6.75, 38)                     # and its "and"


def test_the_notes_follow_a_faster_conductor():
    h = Harness(ScoreProgram(simple_score(), offset_beats=0.0))
    h.run(3.4, beats=[1.0, 1.5, 2.0, 2.5, 3.0])
    h.run(4.0, beats=[3.4, 3.8])                          # speeding up
    times = dict((n, t) for t, n in h.played)
    assert times[65] < 4.0                                # beat 2 came sooner than 4.0
    assert h.source.clock.bpm > 120


def test_a_note_whose_moment_has_passed_is_played_now_or_skipped():
    h = Harness(ScoreProgram(simple_score(), offset_beats=0.0))
    h.run(3.4, beats=[1.0, 1.5, 2.0, 2.5, 3.0])
    # a missed stroke: the next one lands two beats out, so beat 2 is now
    h.run(4.1, beats=[4.0])
    assert h.source.last_stroke.kind == "missed"
    late = [t for t, n in h.played if n in (65, 38)]
    assert late and all(t >= 4.0 for t in late)
    assert h.source.skipped == 0
    # beat 1.5 would have been more than LATE_SKIP_S ago had it existed
    assert LATE_SKIP_S < 0.5


def test_dynamics_scale_the_velocities():
    loud = Harness(ScoreProgram(simple_score(), offset_beats=0.0))
    loud.run(3.4, beats=[1.0, 1.5, 2.0, 2.5, 3.0], strength=1.0)
    soft = Harness(ScoreProgram(simple_score(), offset_beats=0.0))
    soft.run(3.4, beats=[1.0, 1.5, 2.0, 2.5, 3.0], strength=0.1)
    assert loud.transport.received[0].velocity > soft.transport.received[0].velocity
    flat = Harness(ScoreProgram(simple_score(), offset_beats=0.0), dynamics=False)
    flat.run(3.4, beats=[1.0, 1.5, 2.0, 2.5, 3.0], strength=0.1)
    assert flat.transport.received[0].velocity == 100


def test_a_finished_piece_starts_over_on_the_next_count_in():
    h = Harness(ScoreProgram(simple_score(), offset_beats=0.0), count_in=2)
    h.run(3.6, beats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5])      # beats 0..3: the whole piece
    assert h.source.program.finished
    assert h.source.restarts == 0
    gap = RESTART_GAP_S + 1.0
    t0 = 3.5 + gap
    h.run(t0 + 1.6, beats=[t0, t0 + 0.5, t0 + 1.0])
    assert h.source.restarts == 1
    assert (round(t0 + 1.0, 4), 60) in h.played           # beat 0 again


def test_restart_command_goes_back_to_the_top():
    h = Harness(ScoreProgram(simple_score(), offset_beats=0.0), count_in=2)
    h.run(2.6, beats=[1.0, 1.5, 2.0, 2.5])
    played_before = len(h.played)
    h.source.restart()
    h.run(2.7)
    assert h.source.restarts == 1
    assert not h.source.clock.started
    h.run(5.1, beats=[4.0, 4.5, 5.0])
    assert len(h.played) > played_before
    assert (5.0, 60) in h.played


def test_tap_is_a_beat_now():
    h = Harness(ScoreProgram(simple_score(), offset_beats=0.0), count_in=2)
    for t in (1.0, 1.5, 2.0):
        h.now[0] = t
        h.source.tap()
        h.source._tick(t)
    assert h.source.clock.anchor_beat == 0
    assert h.source.clock.bpm == pytest.approx(120.0)


def test_the_improviser_can_be_conducted_too():
    from tutti.core.improv import Improviser

    h = Harness(Improviser(seed=3, xylo=1.0, snare=1.0, tom=0.0), count_in=2)
    h.run(3.1, beats=[1.0, 1.5, 2.0, 2.5, 3.0])
    times = sorted({t for t, _ in h.played})
    # eighth-note steps from beat 0 at 2.0, through the beat after the last stroke
    assert times[:4] == [2.0, 2.25, 2.5, 2.75]
    assert max(times) <= 3.5


def test_metronome_input_delivers_steady_beats():
    now = [0.0]
    got = []
    m = MetronomeInput(120.0, clock=lambda: now[0])
    m.start(lambda t, s: got.append(t))
    try:
        import time
        for _ in range(60):
            now[0] += 0.05
            time.sleep(0.004)
    finally:
        m.stop()
    assert len(got) >= 4
    gaps = [b - a for a, b in zip(got, got[1:])]
    assert all(abs(g - 0.5) < 1e-6 for g in gaps)


def test_source_rejects_a_bad_tempo_range():
    with pytest.raises(ValueError):
        ConductSource(ScoreProgram(simple_score()), min_bpm=200, max_bpm=100)
