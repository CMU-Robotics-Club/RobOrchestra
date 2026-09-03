import pytest

from tutti.core import (
    KEYED,
    POOLED,
    ActuatorModel,
    Instrument,
    NoteEvent,
    PlanError,
    Score,
    max_feasible_scale,
    plan_score,
)
from tutti.core.fleet import ESP32_SNARE, LEGACY_XYLO, bind_by_role


def drum(voices=2, cycle_ms=100.0, spacing_ms=0.0, accepts=(38,)):
    return ActuatorModel(voices=voices, cycle_ms=cycle_ms, spacing_ms=spacing_ms,
                         accepts=frozenset(accepts), voice_mode=POOLED)


def score_of(times, note=38, part_id=1):
    return Score(name="t", events=[
        NoteEvent(part_id=part_id, note=note, velocity=100, time_s=t) for t in times])


def one_bot(model, bot_id="b1", role="snare"):
    return {bot_id: Instrument(bot_id, role, model)}


# model arithmetic

def test_min_gap_is_cycle_over_voices():
    assert drum(voices=2, cycle_ms=100).min_gap_ms == 50.0
    assert drum(voices=1, cycle_ms=100).min_gap_ms == 100.0


def test_spacing_can_be_the_binding_constraint():
    assert drum(voices=4, cycle_ms=100, spacing_ms=40).min_gap_ms == 40.0


def test_documented_fleet_rates():
    # the numbers quoted in .notes/03-instruments.md
    assert ESP32_SNARE.min_gap_ms == pytest.approx(52.5)
    assert ESP32_SNARE.max_rate_hz == pytest.approx(19.05, abs=0.01)


def test_invalid_models_are_rejected():
    with pytest.raises(PlanError):
        ActuatorModel(voices=0, cycle_ms=100, accepts=frozenset())
    with pytest.raises(PlanError):
        ActuatorModel(voices=1, cycle_ms=0, accepts=frozenset())
    with pytest.raises(PlanError):
        ActuatorModel(voices=1, cycle_ms=10, accepts=frozenset(), voice_mode="wat")


# the basic contract

def test_comfortable_spacing_places_everything_unmoved():
    plan = plan_score(score_of([0.0, 1.0, 2.0]), one_bot(drum()), {1: ["b1"]})
    assert plan.feasible
    assert [h.play_at_s for h in plan.hits] == [0.0, 1.0, 2.0]
    assert plan.nudged == []


def test_two_voices_alternate():
    plan = plan_score(score_of([0.0, 0.06]), one_bot(drum()), {1: ["b1"]})
    assert plan.feasible
    assert [h.voice for h in plan.hits] == [0, 1]


def test_third_fast_note_needs_the_first_voice_back():
    # 100ms cycle, 2 voices -> sustainable gap is 50ms. At 60ms it fits.
    plan = plan_score(score_of([0.0, 0.06, 0.12]), one_bot(drum()), {1: ["b1"]})
    assert plan.feasible
    assert [h.voice for h in plan.hits] == [0, 1, 0]


def test_small_overrun_is_nudged_not_dropped():
    # gap 45ms against a 50ms floor: 5ms short, inside the 15ms tolerance
    plan = plan_score(score_of([0.0, 0.045, 0.09]), one_bot(drum()), {1: ["b1"]})
    assert plan.feasible
    nudges = [h.nudge_ms for h in plan.hits]
    assert nudges[0] == 0.0
    assert max(nudges) > 0


def test_nudge_never_exceeds_tolerance():
    plan = plan_score(score_of([0.0, 0.02, 0.04, 0.06]), one_bot(drum()),
                      {1: ["b1"]}, tolerance_ms=15.0)
    assert all(h.nudge_ms <= 15.0 + 1e-9 for h in plan.hits)


def test_impossible_rate_is_dropped_with_a_reason():
    # 10ms apart against a 50ms floor is far outside tolerance
    plan = plan_score(score_of([0.0, 0.01, 0.02]), one_bot(drum()), {1: ["b1"]})
    assert not plan.feasible
    assert plan.drops[0].reason == "cycle_not_ready"
    assert "cycle/voice" in plan.drops[0].detail


def test_nudges_do_not_accumulate_into_drift():
    plan = plan_score(score_of([i * 0.5 for i in range(20)]), one_bot(drum()), {1: ["b1"]})
    assert plan.feasible
    assert all(h.nudge_ms == 0.0 for h in plan.hits)


# spacing, and why it is a separate reason

def test_global_spacing_is_reported_separately():
    model = drum(voices=4, cycle_ms=40, spacing_ms=35)
    plan = plan_score(score_of([0.0, 0.005]), one_bot(model), {1: ["b1"]}, tolerance_ms=1.0)
    assert not plan.feasible
    assert plan.drops[0].reason == "global_spacing"


# routing

def test_note_no_bot_accepts_is_its_own_reason():
    plan = plan_score(score_of([0.0], note=99), one_bot(drum()), {1: ["b1"]})
    assert plan.drops[0].reason == "note_not_accepted"


def test_unbound_part_is_its_own_reason():
    plan = plan_score(score_of([0.0]), one_bot(drum()), {})
    assert plan.drops[0].reason == "no_bot_for_part"


def test_binding_to_an_unknown_bot_raises():
    with pytest.raises(PlanError, match="unknown bot"):
        plan_score(score_of([0.0]), one_bot(drum()), {1: ["ghost"]})


def test_second_bot_absorbs_what_the_first_cannot():
    fleet = {
        "b1": Instrument("b1", "snare", drum()),
        "b2": Instrument("b2", "snare", drum()),
    }
    # 25ms apart: one bot floors at 50ms, two bots give four sticks
    plan = plan_score(score_of([0.0, 0.025, 0.05, 0.075]), fleet, {1: ["b1", "b2"]})
    assert plan.feasible
    assert {h.bot_id for h in plan.hits} == {"b1", "b2"}
    assert plan.reassigned


def test_first_listed_bot_is_preferred():
    fleet = {
        "b1": Instrument("b1", "snare", drum()),
        "b2": Instrument("b2", "snare", drum()),
    }
    plan = plan_score(score_of([0.0, 1.0]), fleet, {1: ["b1", "b2"]})
    assert {h.bot_id for h in plan.hits} == {"b1"}


def test_one_bot_shared_by_two_parts_sees_a_single_timeline():
    model = drum(accepts=(38, 45))
    events = [
        NoteEvent(part_id=1, note=38, velocity=100, time_s=0.0),
        NoteEvent(part_id=2, note=45, velocity=100, time_s=0.001),
        NoteEvent(part_id=1, note=38, velocity=100, time_s=0.002),
    ]
    plan = plan_score(Score(name="t", events=events), one_bot(model),
                      {1: ["b1"], 2: ["b1"]}, tolerance_ms=1.0)
    # two voices absorb the first two; the third has nowhere to go
    assert len(plan.hits) == 2
    assert len(plan.drops) == 1


# keyed instruments

def test_keyed_voices_are_independent_across_keys():
    plan = plan_score(
        Score(name="t", events=[
            NoteEvent(part_id=1, note=60, velocity=100, time_s=0.0),
            NoteEvent(part_id=1, note=62, velocity=100, time_s=0.0),
            NoteEvent(part_id=1, note=64, velocity=100, time_s=0.0),
        ]),
        one_bot(LEGACY_XYLO, role="xylo"), {1: ["b1"]})
    assert plan.feasible
    assert [h.voice for h in plan.hits] == [0, 2, 4]


def test_keyed_repeat_on_one_key_is_still_limited():
    plan = plan_score(score_of([0.0, 0.01], note=60), one_bot(LEGACY_XYLO, role="xylo"),
                      {1: ["b1"]})
    assert not plan.feasible
    assert plan.drops[0].reason == "cycle_not_ready"


def test_keyed_note_outside_the_keyboard_is_not_accepted():
    plan = plan_score(score_of([0.0], note=90), one_bot(LEGACY_XYLO, role="xylo"), {1: ["b1"]})
    assert plan.drops[0].reason == "note_not_accepted"


# tempo scaling and the feasibility search

def test_tempo_scale_compresses_time():
    plan = plan_score(score_of([0.0, 1.0]), one_bot(drum()), {1: ["b1"]}, tempo_scale=0.5)
    assert [h.play_at_s for h in plan.hits] == [0.0, 0.5]


def test_faster_tempo_eventually_breaks():
    s = score_of([0.0, 0.1, 0.2, 0.3])
    assert plan_score(s, one_bot(drum()), {1: ["b1"]}, tempo_scale=1.0).feasible
    assert not plan_score(s, one_bot(drum()), {1: ["b1"]}, tempo_scale=0.1).feasible


def test_max_feasible_scale_is_a_real_boundary():
    s = score_of([0.0, 0.1, 0.2, 0.3])
    fleet, binding = one_bot(drum()), {1: ["b1"]}
    scale = max_feasible_scale(s, fleet, binding)
    assert plan_score(s, fleet, binding, tempo_scale=scale * 1.02).feasible
    assert not plan_score(s, fleet, binding, tempo_scale=scale * 0.9).feasible


def test_invalid_arguments_are_rejected():
    with pytest.raises(PlanError):
        plan_score(score_of([0.0]), one_bot(drum()), {1: ["b1"]}, tolerance_ms=-1)
    with pytest.raises(PlanError):
        plan_score(score_of([0.0]), one_bot(drum()), {1: ["b1"]}, tempo_scale=0)


def test_bind_by_role_collects_every_matching_bot():
    fleet = {
        "a": Instrument("a", "snare", drum()),
        "b": Instrument("b", "snare", drum()),
        "c": Instrument("c", "tom", drum()),
    }
    assert bind_by_role(fleet, {1: "snare"}) == {1: ["a", "b"]}


def test_bind_score_falls_back_to_a_bot_that_accepts_the_notes():
    from tutti.core.fleet import bind_score

    fleet = {
        "tom": Instrument("tom", "tom", drum(accepts=(35, 36, 45))),
        "snare": Instrument("snare", "snare", drum(accepts=(38,))),
    }
    from tutti.core import Part
    score = Score(
        name="t",
        parts=[Part(part_id=1, role="bass")],
        events=[NoteEvent(part_id=1, note=36, velocity=100, time_s=0.0)],
    )
    # no bot has role "bass", but the tom accepts note 36
    assert bind_score(fleet, score) == {1: ["tom"]}


def test_bind_score_prefers_the_matching_role():
    from tutti.core import Part
    from tutti.core.fleet import bind_score

    fleet = {
        "a": Instrument("a", "snare", drum(accepts=(38, 45))),
        "b": Instrument("b", "tom", drum(accepts=(38, 45))),
    }
    score = Score(
        name="t",
        parts=[Part(part_id=1, role="snare")],
        events=[NoteEvent(part_id=1, note=38, velocity=100, time_s=0.0)],
    )
    assert bind_score(fleet, score)[1][0] == "a"


# report

def test_preflight_reports_a_clean_score_as_playable():
    from tutti.core import Part
    from tutti.core.report import preflight

    fleet = one_bot(drum(), role="snare")
    score = Score(name="t", parts=[Part(part_id=1, role="snare")],
                  events=[NoteEvent(part_id=1, note=38, velocity=100, time_s=t)
                          for t in (0.0, 1.0, 2.0)],
                  initial_bpm=120.0)
    text = "\n".join(preflight(score, fleet, {1: ["b1"]}))
    assert "all clear" in text
    assert "Playable as written" in text


def test_preflight_names_the_drop_reason_and_a_max_tempo():
    from tutti.core import Part
    from tutti.core.report import preflight

    fleet = one_bot(drum(), role="snare")
    score = Score(name="t", parts=[Part(part_id=1, role="snare")],
                  events=[NoteEvent(part_id=1, note=38, velocity=100, time_s=t)
                          for t in (0.0, 0.01, 0.02)],
                  initial_bpm=120.0)
    text = "\n".join(preflight(score, fleet, {1: ["b1"]}))
    assert "DROP cycle_not_ready" in text
    assert "NOT playable" in text
    assert "Max feasible tempo" in text


def test_preflight_flags_an_unbound_part():
    from tutti.core import Part
    from tutti.core.report import preflight

    score = Score(name="t", parts=[Part(part_id=1, role="tuba")],
                  events=[NoteEvent(part_id=1, note=38, velocity=100, time_s=0.0)],
                  initial_bpm=120.0)
    text = "\n".join(preflight(score, one_bot(drum()), {}))
    assert "NOTHING BOUND" in text


def test_lower_bound_is_reported_as_a_bound_not_a_number():
    from tutti.core import Part
    from tutti.core.report import preflight

    fleet = one_bot(drum(), role="snare")
    score = Score(name="t", parts=[Part(part_id=1, role="snare")],
                  events=[NoteEvent(part_id=1, note=38, velocity=100, time_s=t)
                          for t in (0.0, 10.0)],
                  initial_bpm=120.0)
    text = "\n".join(preflight(score, fleet, {1: ["b1"]}))
    assert "beyond" in text
