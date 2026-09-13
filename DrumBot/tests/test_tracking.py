"""Tests for tracking: kinematics, strike detection, zone mapping, gesture routing."""

from __future__ import annotations

import pytest

from tracking import (
    GestureRouter,
    HandState,
    HandStateStore,
    HitDetector,
    MotionSample,
    StrikeDetector,
    StrikePlaneEstimator,
    ZoneHitGate,
    ZoneMapper,
    fit_kinematics,
    select_fit_window,
    strike_point,
    time_to_plane,
)


# ── Zone mapping ─────────────────────────────────────────────────────

def test_zone_for_x_boundaries() -> None:
    m = ZoneMapper(zone_edges=(0.5,), zone_labels=("SNARE", "TOM"))
    assert m.zone_for_x(0.00) == "SNARE"
    assert m.zone_for_x(0.49) == "SNARE"
    assert m.zone_for_x(0.50) == "TOM"
    assert m.zone_for_x(1.00) == "TOM"


def test_zone_for_x_clamps_out_of_range() -> None:
    m = ZoneMapper(zone_edges=(0.5,), zone_labels=("SNARE", "TOM"))
    assert m.zone_for_x(-1.0) == "SNARE"
    assert m.zone_for_x(2.0) == "TOM"


def test_zone_mapper_supports_adaptive_bot_counts() -> None:
    m = ZoneMapper(zone_edges=(1.0 / 3.0, 2.0 / 3.0), zone_labels=("BOT_1", "BOT_2", "BOT_3"))
    assert m.zone_for_x(0.10) == "BOT_1"
    assert m.zone_for_x(0.50) == "BOT_2"
    assert m.zone_for_x(0.90) == "BOT_3"


def test_invalid_zone_edges_raise() -> None:
    with pytest.raises(ValueError):
        ZoneMapper(zone_edges=(0.5, 0.4), zone_labels=("A", "B", "C"))
    with pytest.raises(ValueError):
        ZoneMapper(zone_edges=(0.2, 1.2), zone_labels=("A", "B", "C"))


# ── Kinematics ───────────────────────────────────────────────────────

def _samples(points: list[tuple[int, float, float]]) -> list[MotionSample]:
    return [MotionSample(timestamp_ms=t, x=x, y=y) for t, x, y in points]


def test_fit_recovers_constant_velocity() -> None:
    # y advances 0.02 every 10 ms -> 2.0 units/s.
    pts = [(t, 0.5, 0.1 + 0.002 * t) for t in range(0, 50, 10)]
    kin = fit_kinematics(_samples(pts))
    assert kin is not None
    assert kin.vy == pytest.approx(2.0, abs=1e-6)
    assert kin.ay == pytest.approx(0.0, abs=1e-6)
    assert kin.y == pytest.approx(0.1 + 0.002 * 40, abs=1e-6)


def test_fit_recovers_constant_acceleration() -> None:
    # y = 0.1 + 1.0 t + 0.5 * 8.0 t^2  ->  v(t) = 1.0 + 8.0 t, a = 8.0
    pts = []
    for step in range(6):
        t_s = step * 0.01
        pts.append((step * 10, 0.5, 0.1 + 1.0 * t_s + 0.5 * 8.0 * t_s * t_s))
    kin = fit_kinematics(_samples(pts))
    assert kin is not None
    assert kin.ay == pytest.approx(8.0, abs=1e-4)
    assert kin.vy == pytest.approx(1.0 + 8.0 * 0.05, abs=1e-4)


def test_fit_smooths_landmark_jitter() -> None:
    """A five-point fit must reject noise that a two-point difference amplifies."""

    true_v = 1.0
    jitter = [0.0, +0.004, -0.004, +0.004, -0.004]
    pts = [(i * 10, 0.5, 0.2 + true_v * (i * 0.01) + jitter[i]) for i in range(5)]
    kin = fit_kinematics(_samples(pts))
    assert kin is not None

    two_point_v = (pts[-1][2] - pts[-2][2]) / 0.01
    assert abs(two_point_v - true_v) > 0.5          # naive estimate is badly wrong
    assert abs(kin.vy - true_v) < abs(two_point_v - true_v)


def test_three_point_fit_does_not_invent_a_positive_slope() -> None:
    """A decelerating rise must never read as descending.

    Fitting a quadratic to exactly three points interpolates them, so a
    flattening rise yields a spuriously positive endpoint slope -- which arms a
    phantom stroke and fires a second hit on the way back up.
    """

    pts = [(3100, 0.5, 0.670), (3117, 0.5, 0.605), (3133, 0.5, 0.594)]
    kin = fit_kinematics(_samples(pts))
    assert kin is not None
    assert kin.vy < 0.0, f"rising hand reported as descending (vy={kin.vy})"


def test_three_point_fit_is_linear() -> None:
    """Three samples must smooth, so no curvature is claimed from them."""

    pts = [(0, 0.5, 0.20), (10, 0.5, 0.26), (20, 0.5, 0.30)]
    kin = fit_kinematics(_samples(pts))
    assert kin is not None
    assert kin.ay == 0.0


def test_rising_hand_never_fires_on_the_way_up() -> None:
    d = _detector()
    s = HandState(hand_id=0, handedness="Left", history_size=8)
    _, t = _stroke(d, s, 0)

    _, t = _feed(d, s, t, 0.25, 0.68, duration_ms=140)   # strike
    # Decelerating lift: y still high but unambiguously rising.
    hits = []
    for y in (0.670, 0.640, 0.605, 0.594, 0.560, 0.500):
        hit = d.update(s, _landmarks(0.4, y), t)
        if hit is not None:
            hits.append(hit)
        t += 16
    assert hits == [], "fired while the hand was lifting"


def test_fit_requires_two_samples() -> None:
    assert fit_kinematics(_samples([(0, 0.5, 0.2)])) is None


def test_fit_rejects_zero_span() -> None:
    assert fit_kinematics(_samples([(5, 0.5, 0.2), (5, 0.5, 0.3)])) is None


def test_fit_window_stops_at_a_direction_reversal() -> None:
    """A fit must not straddle a turnaround and read the corner as curvature."""

    pts = [(0, 0.5, 0.20), (10, 0.5, 0.30), (20, 0.5, 0.40), (30, 0.5, 0.32), (40, 0.5, 0.22)]
    window = select_fit_window(_samples(pts), max_length=5)
    assert [s.y for s in window] == [0.40, 0.32, 0.22]


def test_fit_window_keeps_full_span_without_reversal() -> None:
    pts = [(i * 10, 0.5, 0.20 + 0.05 * i) for i in range(5)]
    window = select_fit_window(_samples(pts), max_length=5)
    assert len(window) == 5


def test_fit_window_deadband_ignores_jitter() -> None:
    """Sub-deadband wobble during steady motion must not truncate the window."""

    pts = [(i * 10, 0.5, 0.20 + 0.05 * i + (0.0008 if i % 2 else -0.0008)) for i in range(5)]
    window = select_fit_window(_samples(pts), max_length=5, deadband=0.002)
    assert len(window) == 5


def test_fit_window_across_reversal_fixes_acceleration_blowup() -> None:
    # Straight down, turn, then straight back up at a constant rate.
    pts = [(0, 0.5, 0.20), (16, 0.5, 0.40), (32, 0.5, 0.60), (48, 0.5, 0.40), (64, 0.5, 0.20)]
    naive = fit_kinematics(_samples(pts))
    trimmed = fit_kinematics(select_fit_window(_samples(pts), max_length=5))
    assert naive is not None and trimmed is not None
    assert abs(naive.ay) > 100.0            # corner read as huge curvature
    assert abs(trimmed.ay) < 1e-6           # clean straight line after the turn


# ── Time to plane ────────────────────────────────────────────────────

def test_time_to_plane_constant_velocity() -> None:
    assert time_to_plane(y=0.2, vy=2.0, ay=0.0, plane=0.6) == pytest.approx(0.2)


def test_time_to_plane_accounts_for_acceleration() -> None:
    accelerating = time_to_plane(y=0.2, vy=2.0, ay=10.0, plane=0.6)
    assert accelerating is not None
    assert accelerating < 0.2                       # speeding up arrives sooner


def test_time_to_plane_zero_when_already_past() -> None:
    assert time_to_plane(y=0.7, vy=2.0, ay=0.0, plane=0.6) == 0.0


def test_time_to_plane_none_when_not_descending() -> None:
    assert time_to_plane(y=0.2, vy=-2.0, ay=0.0, plane=0.6) is None


# ── Strike point ─────────────────────────────────────────────────────

def test_palm_centroid_averages_palm_landmarks() -> None:
    lms = [(0.0, 0.0, 0.0)] * 21
    for idx in (0, 5, 9, 13, 17):
        lms[idx] = (1.0, 0.5, 0.0)
    x, y = strike_point(lms, mode="palm_centroid")
    assert x == pytest.approx(1.0)
    assert y == pytest.approx(0.5)


def test_palm_centroid_is_steadier_than_single_landmark() -> None:
    """Finger articulation must not move the strike point."""

    base = [(0.5, 0.5, 0.0)] * 21
    curled = list(base)
    curled[9] = (0.5, 0.62, 0.0)                    # middle knuckle shifts alone

    _, y_single_base = strike_point(base, mode="landmark", landmark_index=9)
    _, y_single_curl = strike_point(curled, mode="landmark", landmark_index=9)
    _, y_palm_base = strike_point(base, mode="palm_centroid")
    _, y_palm_curl = strike_point(curled, mode="palm_centroid")

    assert abs(y_single_curl - y_single_base) == pytest.approx(0.12)
    assert abs(y_palm_curl - y_palm_base) < 0.03


# ── Stroke simulation ────────────────────────────────────────────────

def _landmarks(x: float, y: float) -> tuple[tuple[float, float, float], ...]:
    return tuple((x, y, 0.0) for _ in range(21))


def _feed(
    detector: StrikeDetector,
    state: HandState,
    start_ms: int,
    y_from: float,
    y_to: float,
    duration_ms: int,
    dt_ms: int = 16,
    x: float = 0.4,
) -> tuple[list, int]:
    """Feed a linear ramp of samples; return (hits, next timestamp)."""

    hits = []
    steps = max(duration_ms // dt_ms, 1)
    t = start_ms
    for i in range(steps + 1):
        y = y_from + (y_to - y_from) * (i / steps)
        hit = detector.update(state, _landmarks(x, y), t)
        if hit is not None:
            hits.append(hit)
        t += dt_ms
    return hits, t


def _lift(detector: StrikeDetector, state: HandState, start_ms: int, top: float = 0.25, bottom: float = 0.65) -> int:
    """Raise the hand into playing position.

    A strike requires a preparatory lift, which is what a player actually does
    before the first beat, so fixtures must perform one before striking.
    """

    _, t = _feed(detector, state, start_ms, bottom, top, duration_ms=180)
    return t


def _stroke(detector: StrikeDetector, state: HandState, start_ms: int, top: float = 0.25, bottom: float = 0.65):
    """One full down-then-up drum stroke."""

    down_hits, t = _feed(detector, state, start_ms, top, bottom, duration_ms=140)
    up_hits, t = _feed(detector, state, t, bottom, top, duration_ms=180)
    return down_hits + up_hits, t


def _detector(**overrides) -> StrikeDetector:
    kwargs = dict(
        latency_compensation_ms=90,
        arm_velocity=0.45,
        min_travel=0.035,
        refractory_ms=55,
        plane_estimator=StrikePlaneEstimator(alpha=0.4),
    )
    kwargs.update(overrides)
    return StrikeDetector(**kwargs)


# ── Strike detection ─────────────────────────────────────────────────

def test_emits_exactly_one_hit_per_stroke() -> None:
    d = _detector()
    s = HandState(hand_id=0, handedness="Left", history_size=8)

    t = _lift(d, s, 0)
    counts = []
    for _ in range(4):
        hits, t = _stroke(d, s, t)
        counts.append(len(hits))

    assert counts == [1, 1, 1, 1], f"expected one hit per stroke, got {counts}"


def test_jitter_at_the_trigger_point_cannot_double_fire() -> None:
    """The hand must physically lift before another strike is allowed."""

    d = _detector()
    s = HandState(hand_id=0, handedness="Left", history_size=8)

    t = _lift(d, s, 0)
    hits, t = _feed(d, s, t, 0.25, 0.65, duration_ms=140)
    assert len(hits) == 1

    # Hover and shake around the bottom without ever lifting.
    extra = []
    for i in range(30):
        y = 0.65 + (0.004 if i % 2 else -0.004)
        hit = d.update(s, _landmarks(0.4, y), t)
        if hit is not None:
            extra.append(hit)
        t += 16
    assert extra == []


def test_lifting_rearms_for_the_next_hit() -> None:
    d = _detector()
    s = HandState(hand_id=0, handedness="Left", history_size=8)

    t = _lift(d, s, 0)
    first, t = _feed(d, s, t, 0.25, 0.65, duration_ms=140)
    assert len(first) == 1

    _, t = _feed(d, s, t, 0.65, 0.25, duration_ms=180)      # lift
    second, t = _feed(d, s, t, 0.25, 0.65, duration_ms=140)  # strike again
    assert len(second) == 1


def test_fires_ahead_of_predicted_impact() -> None:
    """Once the plane is learned the note must lead the impact."""

    d = _detector(latency_compensation_ms=80)
    s = HandState(hand_id=0, handedness="Left", history_size=8)

    _, t = _stroke(d, s, 0)                 # teaches the plane
    assert s.strike_plane is not None

    hits, t = _feed(d, s, t, 0.25, 0.65, duration_ms=140)
    assert len(hits) == 1
    hit = hits[0]
    assert hit.lead_ms > 0, "predictive detector fired at impact, not ahead of it"
    assert hit.lead_ms <= 80
    assert hit.y < s.strike_plane, "fired after the hand already passed the plane"


def test_higher_latency_compensation_fires_earlier() -> None:
    def lead_for(latency_ms: int) -> int:
        d = _detector(latency_compensation_ms=latency_ms)
        s = HandState(hand_id=0, handedness="Left", history_size=8)
        _, t = _stroke(d, s, 0)
        hits, _ = _feed(d, s, t, 0.25, 0.65, duration_ms=140)
        assert len(hits) == 1
        return hits[0].lead_ms

    assert lead_for(110) > lead_for(40)


def test_idle_hand_lowered_to_rest_does_not_fire() -> None:
    """The bug this rule exists for.

    A hand that has never played has no strike plane of its own, so it borrows
    the other hand's. Lowering it out of the way must not be read as a strike.
    """

    planes = StrikePlaneEstimator(alpha=0.3)
    d = _detector(plane_estimator=planes)

    playing = HandState(hand_id=0, handedness="Left", history_size=8)
    t = _lift(d, playing, 0)
    for _ in range(4):
        _, t = _stroke(d, playing, t)
    assert planes.global_plane is not None

    idle = HandState(hand_id=1, handedness="Right", history_size=8)
    assert idle.strike_plane is None

    hits = []
    for i in range(20):                       # held still, up high
        hit = d.update(idle, _landmarks(0.8, 0.30), t)
        if hit is not None:
            hits.append(hit)
        t += 16
    for i in range(40):                       # lowered smoothly to rest
        hit = d.update(idle, _landmarks(0.8, 0.30 + 0.50 * (i / 39)), t)
        if hit is not None:
            hits.append(hit)
        t += 16

    assert hits == [], f"idle hand fired {len(hits)} phantom hit(s) while being lowered"


def test_cold_start_descent_does_not_fire() -> None:
    d = _detector()
    s = HandState(hand_id=0, handedness="Left", history_size=8)
    hits, _ = _feed(d, s, 0, 0.25, 0.65, duration_ms=140)
    assert hits == []


def test_descent_after_a_lift_does_fire() -> None:
    d = _detector()
    s = HandState(hand_id=0, handedness="Left", history_size=8)
    t = _lift(d, s, 0)
    hits, _ = _feed(d, s, t, 0.25, 0.65, duration_ms=140)
    assert len(hits) == 1


def test_hands_at_different_heights_keep_separate_planes() -> None:
    """One hand playing high and one low must not contaminate each other."""

    planes = StrikePlaneEstimator(alpha=0.3)
    d = _detector(plane_estimator=planes)

    low = HandState(hand_id=0, handedness="Left", history_size=8)
    high = HandState(hand_id=1, handedness="Right", history_size=8)

    t = _lift(d, low, 0)
    for _ in range(4):
        _, t = _stroke(d, low, t, top=0.25, bottom=0.65)

    t2 = _lift(d, high, 0, top=0.08, bottom=0.38)
    for _ in range(4):
        _, t2 = _stroke(d, high, t2, top=0.08, bottom=0.38)

    assert low.strike_plane == pytest.approx(0.65, abs=0.05)
    assert high.strike_plane == pytest.approx(0.38, abs=0.05)


def test_small_jitter_never_triggers_a_hit() -> None:
    d = _detector()
    s = HandState(hand_id=0, handedness="Left", history_size=8)

    t = 0
    hits = []
    for i in range(60):
        y = 0.45 + (0.006 if i % 2 else -0.006)
        hit = d.update(s, _landmarks(0.4, y), t)
        if hit is not None:
            hits.append(hit)
        t += 16
    assert hits == []


def test_aborted_stroke_does_not_fire() -> None:
    """A downstroke that stops short of the travel threshold produces nothing."""

    d = _detector(min_travel=0.20)
    s = HandState(hand_id=0, handedness="Left", history_size=8)
    t = _lift(d, s, 0, top=0.30, bottom=0.60)
    hits, _ = _feed(d, s, t, 0.30, 0.36, duration_ms=90)
    assert hits == []


def test_velocity_scales_with_stroke_speed() -> None:
    # A wide cap keeps both strokes inside the linear range, so this exercises
    # the velocity mapping rather than the clamp.
    def velocity_for(duration_ms: int) -> float:
        d = _detector(velocity_cap=6.0)
        s = HandState(hand_id=0, handedness="Left", history_size=8)
        _, t = _stroke(d, s, 0)
        hits, _ = _feed(d, s, t, 0.25, 0.65, duration_ms=duration_ms)
        assert len(hits) == 1
        return hits[0].velocity

    assert velocity_for(80) > velocity_for(220)


def test_reported_x_is_projected_to_impact() -> None:
    """Zone assignment should use where the strike lands, not where it started."""

    d = _detector()
    s = HandState(hand_id=0, handedness="Left", history_size=8)
    _, t = _stroke(d, s, 0)

    # Descend while drifting right, so the impact point leads the current x.
    hits = []
    steps = 9
    for i in range(steps + 1):
        y = 0.25 + (0.65 - 0.25) * (i / steps)
        x = 0.30 + 0.30 * (i / steps)
        hit = d.update(s, _landmarks(x, y), t)
        if hit is not None:
            hits.append((hit, x))
        t += 16

    assert len(hits) == 1
    hit, x_at_fire = hits[0]
    assert hit.x > x_at_fire, "predicted impact x should lead the current x"
    assert 0.0 <= hit.x <= 1.0


def test_refractory_floor_is_respected() -> None:
    d = _detector(refractory_ms=120, min_travel=0.01, rearm_travel=0.001)
    s = HandState(hand_id=0, handedness="Left", history_size=8)

    t = _lift(d, s, 0)
    first, t = _feed(d, s, t, 0.25, 0.65, duration_ms=140)
    assert len(first) == 1
    fired_at = first[0].timestamp_ms

    _, t = _feed(d, s, t, 0.65, 0.60, duration_ms=16)
    second, _ = _feed(d, s, t, 0.60, 0.90, duration_ms=48)
    for hit in second:
        assert hit.timestamp_ms - fired_at >= 120


# ── Strike plane estimation ──────────────────────────────────────────

def test_plane_estimator_learns_turnaround_height() -> None:
    d = _detector()
    s = HandState(hand_id=0, handedness="Left", history_size=8)

    t = 0
    for _ in range(4):
        _, t = _stroke(d, s, t, top=0.20, bottom=0.70)

    assert s.strike_plane is not None
    assert s.strike_plane == pytest.approx(0.70, abs=0.05)


def test_plane_estimator_adapts_when_the_player_moves() -> None:
    d = _detector()
    s = HandState(hand_id=0, handedness="Left", history_size=8)

    t = 0
    for _ in range(3):
        _, t = _stroke(d, s, t, top=0.10, bottom=0.45)
    high = s.strike_plane

    for _ in range(6):
        _, t = _stroke(d, s, t, top=0.40, bottom=0.85)
    low = s.strike_plane

    assert high is not None and low is not None
    assert low > high + 0.2


def test_global_plane_seeds_a_newly_seen_hand() -> None:
    planes = StrikePlaneEstimator(alpha=0.4, min_observations=1)
    d = _detector(plane_estimator=planes)

    left = HandState(hand_id=0, handedness="Left", history_size=8)
    _, t = _stroke(d, left, 0)
    assert planes.global_plane is not None

    right = HandState(hand_id=1, handedness="Right", history_size=8)
    assert right.strike_plane is None
    assert planes.plane_for(right) == pytest.approx(planes.global_plane)


def test_seeded_plane_is_used_before_any_stroke() -> None:
    planes = StrikePlaneEstimator(alpha=0.25, initial=0.6)
    assert planes.global_plane == pytest.approx(0.6)


# ── Hand state store ─────────────────────────────────────────────────

def test_gap_in_tracking_resets_motion_history() -> None:
    """Stale samples across a tracking gap must not synthesise a strike."""

    store = HandStateStore(history_size=8, gap_reset_ms=200)
    state = store.get_or_create(0, "Left", 1000)
    state.add_sample(MotionSample(timestamp_ms=1000, x=0.4, y=0.2))
    state.last_velocity = 5.0

    same = store.get_or_create(0, "Left", 1400)
    assert same is state
    assert len(state.samples) == 0
    assert state.last_velocity == 0.0


def test_short_gap_preserves_history() -> None:
    store = HandStateStore(history_size=8, gap_reset_ms=200)
    state = store.get_or_create(0, "Left", 1000)
    state.add_sample(MotionSample(timestamp_ms=1000, x=0.4, y=0.2))

    store.get_or_create(0, "Left", 1050)
    assert len(state.samples) == 1


def test_prune_stale_removes_absent_hands() -> None:
    store = HandStateStore(history_size=8)
    state = store.get_or_create(0, "Left", 1000)
    state.add_sample(MotionSample(timestamp_ms=1000, x=0.4, y=0.2))
    store.prune_stale(current_timestamp_ms=5000)
    assert store.get_or_create(0, "Left", 5000) is not state


# ── Legacy detector (kept for A/B against the predictive one) ─────────

def test_legacy_detects_hit_on_downward_velocity_crossing() -> None:
    d = HitDetector(min_travel=0.03, velocity_threshold=1.0, cooldown_ms=120, velocity_cap=2.5)
    s = HandState(hand_id=0, handedness="Left", history_size=8)
    assert d.update(s, _landmarks(0.40, 0.20), 0) is None
    assert d.update(s, _landmarks(0.40, 0.22), 33) is None
    hit = d.update(s, _landmarks(0.40, 0.30), 66)
    assert hit is not None
    assert hit.handedness == "Left"
    assert 0.0 <= hit.velocity <= 1.0


def test_legacy_applies_cooldown_between_hits() -> None:
    d = HitDetector(min_travel=0.03, velocity_threshold=1.0, cooldown_ms=120, velocity_cap=2.5)
    s = HandState(hand_id=1, handedness="Right", history_size=8)
    d.update(s, _landmarks(0.65, 0.20), 0)
    d.update(s, _landmarks(0.65, 0.22), 33)
    assert d.update(s, _landmarks(0.65, 0.30), 66) is not None
    d.update(s, _landmarks(0.65, 0.31), 99)
    assert d.update(s, _landmarks(0.65, 0.40), 132) is None
    d.update(s, _landmarks(0.65, 0.41), 220)
    assert d.update(s, _landmarks(0.65, 0.50), 253) is not None


def test_legacy_requires_minimum_travel() -> None:
    d = HitDetector(min_travel=0.05, velocity_threshold=1.0, cooldown_ms=120, velocity_cap=2.5)
    s = HandState(hand_id=2, handedness="Left", history_size=8)
    d.update(s, _landmarks(0.20, 0.20), 0)
    d.update(s, _landmarks(0.20, 0.205), 33)
    assert d.update(s, _landmarks(0.20, 0.24), 66) is None


# ── Hit gating ────────────────────────────────────────────────────────

def test_zone_hit_gate_applies_per_zone_cooldown() -> None:
    gate = ZoneHitGate(cooldown_ms=40)
    assert gate.should_emit("SNARE", 1000) is True
    assert gate.should_emit("SNARE", 1010) is False
    assert gate.should_emit("SNARE", 1040) is True


def test_zone_hit_gate_does_not_block_other_zones() -> None:
    gate = ZoneHitGate(cooldown_ms=40)
    assert gate.should_emit("SNARE", 1000) is True
    assert gate.should_emit("TOM", 1000) is True


# ── Gesture routing ──────────────────────────────────────────────────

def _router() -> GestureRouter:
    return GestureRouter(label_to_command={"Open_Palm": "ARM", "Closed_Fist": "STOP"}, cooldown_ms=500)


def test_routes_known_label() -> None:
    r = _router()
    e = r.route(label="Open_Palm", handedness="Left", timestamp_ms=1000)
    assert e is not None
    assert e.command == "ARM"


def test_unknown_label_produces_nothing() -> None:
    assert _router().route(label="Victory", handedness="Left", timestamp_ms=1000) is None


def test_cooldown_blocks_repeats() -> None:
    r = _router()
    assert r.route("Closed_Fist", "Right", 1000) is not None
    assert r.route("Closed_Fist", "Right", 1200) is None
    assert r.route("Closed_Fist", "Right", 1600) is not None


def test_cooldown_independent_per_hand() -> None:
    r = _router()
    assert r.route("Open_Palm", "Left", 1000) is not None
    assert r.route("Open_Palm", "Right", 1000) is not None
