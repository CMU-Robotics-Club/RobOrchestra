"""Hand tracking, strike detection, zone mapping, and gesture routing.

Two detectors live here:

- ``HitDetector``   legacy two-point velocity-threshold crossing (kept for A/B).
- ``StrikeDetector`` predictive time-to-contact detector (default).

The predictive detector exists because the drum is physically ~90-160 ms behind
the camera (MediaPipe inference + BLE MIDI + servo travel). Detecting the strike
*at* impact therefore always sounds late. Instead we fit local kinematics to the
hand, extrapolate to an adaptively-learned strike plane, and fire when the
predicted impact is exactly one system-latency away.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Mapping, Sequence

# Landmarks forming the palm: wrist + the four finger MCP knuckles. Averaging
# these is far steadier than any single landmark, which jitters when fingers
# articulate mid-stroke.
PALM_LANDMARK_INDICES: tuple[int, ...] = (0, 5, 9, 13, 17)
DEFAULT_STRIKE_LANDMARK = 9


# ── Kinematics ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class Kinematics:
    """Local motion estimate evaluated at the newest sample."""

    y: float
    vy: float
    ay: float
    vx: float


def _solve3(m: list[list[float]], rhs: list[float]) -> tuple[float, float, float] | None:
    """Solve a 3x3 system by Cramer's rule; None when near-singular."""

    def det3(a: list[list[float]]) -> float:
        return (
            a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
            - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
            + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
        )

    base = det3(m)
    if abs(base) < 1e-12:
        return None

    out: list[float] = []
    for col in range(3):
        swapped = [[rhs[r] if c == col else m[r][c] for c in range(3)] for r in range(3)]
        out.append(det3(swapped) / base)
    return out[0], out[1], out[2]


def fit_kinematics(samples: Sequence["MotionSample"]) -> Kinematics | None:
    """Least-squares local fit over recent samples, evaluated at the newest one.

    The polynomial degree tracks the sample count so the fit always stays
    over-determined, and therefore always smooths: four or more samples get a
    quadratic, three get a line, and two fall back to a finite difference.
    Fitting a quadratic to three points would interpolate them exactly and
    reject no noise whatsoever.
    """

    n = len(samples)
    if n < 2:
        return None

    times = [s.timestamp_ms / 1000.0 for s in samples]
    t_end = times[-1]
    span = t_end - times[0]
    if span <= 0.0:
        return None

    if n == 2:
        dt = times[1] - times[0]
        if dt <= 0.0:
            return None
        return Kinematics(
            y=samples[-1].y,
            vy=(samples[1].y - samples[0].y) / dt,
            ay=0.0,
            vx=(samples[1].x - samples[0].x) / dt,
        )

    # Centering on the mean time keeps the normal equations well conditioned.
    t_mean = sum(times) / n
    u = [t - t_mean for t in times]
    delta = t_end - t_mean

    if n == 3:
        # A quadratic through three points interpolates them exactly and so
        # rejects no noise at all -- it will happily report a positive slope for
        # a decelerating rise and arm a phantom stroke. A line through three
        # points is over-determined, so it actually smooths.
        denom = sum(v * v for v in u)
        if denom <= 0.0:
            return None

        def linear_slope(values: Sequence[float]) -> float:
            return sum(v * val for v, val in zip(u, values)) / denom

        ys = [s.y for s in samples]
        slope = linear_slope(ys)
        return Kinematics(
            y=(sum(ys) / n) + slope * delta,
            vy=slope,
            ay=0.0,
            vx=linear_slope([s.x for s in samples]),
        )

    s0 = float(n)
    s1 = sum(u)
    s2 = sum(v * v for v in u)
    s3 = sum(v ** 3 for v in u)
    s4 = sum(v ** 4 for v in u)
    matrix = [[s0, s1, s2], [s1, s2, s3], [s2, s3, s4]]

    def fit_axis(values: Sequence[float]) -> tuple[float, float, float] | None:
        rhs = [
            sum(values),
            sum(v * val for v, val in zip(u, values)),
            sum(v * v * val for v, val in zip(u, values)),
        ]
        return _solve3(matrix, rhs)

    y_coeffs = fit_axis([s.y for s in samples])
    if y_coeffs is None:
        return None
    a, b, c = y_coeffs

    y = a + b * delta + c * delta * delta
    vy = b + 2.0 * c * delta
    ay = 2.0 * c

    vx = 0.0
    x_coeffs = fit_axis([s.x for s in samples])
    if x_coeffs is not None:
        vx = x_coeffs[1] + 2.0 * x_coeffs[2] * delta

    return Kinematics(y=y, vy=vy, ay=ay, vx=vx)


def select_fit_window(
    samples: Sequence["MotionSample"],
    max_length: int,
    deadband: float = 0.002,
) -> list["MotionSample"]:
    """Take the newest samples, stopping at the last real direction reversal.

    Fitting one polynomial across a turnaround treats a corner in the
    trajectory as curvature, which throws the acceleration estimate wildly off
    and drags the velocity with it. The deadband keeps landmark jitter from
    being mistaken for a reversal during slow motion.
    """

    window = list(samples)[-max_length:]
    if len(window) <= 2:
        return window

    deltas = [window[i + 1].y - window[i].y for i in range(len(window) - 1)]

    reference = 0
    for delta in reversed(deltas):
        if abs(delta) > deadband:
            reference = 1 if delta > 0 else -1
            break
    if reference == 0:
        return window

    cut = 0
    for i in range(len(deltas) - 1, -1, -1):
        delta = deltas[i]
        if abs(delta) > deadband and (1 if delta > 0 else -1) != reference:
            cut = i + 1
            break

    trimmed = window[cut:]
    return trimmed if len(trimmed) >= 2 else window[-2:]


def time_to_plane(y: float, vy: float, ay: float, plane: float, use_acceleration: bool = True) -> float | None:
    """Seconds until the modelled trajectory crosses ``plane``.

    Returns 0.0 when the plane has already been passed while descending, and
    None when the trajectory is not descending or decelerates to a stop before
    ever reaching the plane.
    """

    if vy <= 0.0:
        return None
    if y >= plane:
        return 0.0

    offset = y - plane
    if use_acceleration and abs(ay) > 1e-6:
        disc = vy * vy - 2.0 * ay * offset
        if disc < 0.0:
            # Decelerating too hard to ever arrive.
            return None
        root = disc ** 0.5
        positives = [t for t in ((-vy + root) / ay, (-vy - root) / ay) if t > 0.0]
        return min(positives) if positives else None

    return -offset / vy


def time_to_turnaround(vy: float, ay: float) -> float | None:
    """Seconds until a decelerating descent reaches zero velocity."""

    if vy <= 0.0 or ay >= -1e-6:
        return None
    return -vy / ay


def time_to_impact_harmonic(y: float, vy: float, top: float, bottom: float) -> float | None:
    """Seconds to the bottom of the stroke, modelling it as simple harmonic motion.

    A drum stroke is a smooth reversal, so the hand eases into its turnaround
    rather than arriving at the speed it had mid-descent. Extrapolating a
    straight line (or the mid-stroke acceleration) therefore predicts impact
    too early, and the error grows with stroke length. Treating the stroke as
    one half-cycle of ``y = mid - amp*cos(theta)`` uses only position and
    velocity -- no noisy acceleration term -- and stays accurate on asymmetric
    and sharply-accelerating strokes alike.
    """

    if vy <= 0.0:
        return None

    amplitude = (bottom - top) / 2.0
    if amplitude <= 1e-4:
        return None

    midpoint = (top + bottom) / 2.0
    cosine = min(max(-(y - midpoint) / amplitude, -1.0), 1.0)
    theta = math.acos(cosine)          # 0 at the top of the stroke, pi at the bottom
    sine = math.sin(theta)
    if sine <= 1e-6:
        return 0.0

    # omega = vy / (amp * sin(theta)), and the bottom is at theta = pi.
    return (math.pi - theta) * amplitude * sine / vy


def time_to_impact(
    y: float,
    vy: float,
    ay: float,
    plane: float | None,
    use_acceleration: bool = True,
) -> float | None:
    """Seconds until the stroke bottoms out.

    A stroke ends either by crossing the learned strike plane or by
    decelerating to a standstill, whichever comes first. Considering only the
    plane makes the detector fire far too early on slow strokes, because a hand
    easing into its turnaround covers the last stretch much more slowly than a
    constant-velocity extrapolation assumes.
    """

    if vy <= 0.0:
        return None

    candidates: list[float] = []

    if plane is not None:
        if y >= plane:
            return 0.0
        crossing = time_to_plane(y, vy, ay, plane, use_acceleration=use_acceleration)
        if crossing is not None:
            candidates.append(crossing)

    if use_acceleration:
        stopping = time_to_turnaround(vy, ay)
        if stopping is not None:
            candidates.append(stopping)

    if candidates:
        return min(candidates)
    if plane is None:
        return None
    return -(y - plane) / vy


# ── Hand state ───────────────────────────────────────────────────────

# Strike phases.
PHASE_READY = "READY"
PHASE_ARMED = "ARMED"
PHASE_FIRED = "FIRED"


@dataclass
class MotionSample:
    timestamp_ms: int
    x: float
    y: float


@dataclass
class HandState:
    hand_id: int
    handedness: str
    history_size: int
    samples: deque[MotionSample] = field(init=False)
    last_velocity: float = 0.0
    last_hit_timestamp_ms: int = -1
    last_seen_timestamp_ms: int = -1

    # Predictive detector state.
    phase: str = PHASE_READY
    stroke_start_y: float = 0.0
    stroke_peak_velocity: float = 0.0
    fired_y: float = 0.0
    strike_plane: float | None = None
    stroke_top: float | None = None
    descent_max_y: float | None = None
    ascent_min_y: float | None = None
    lift_seen: bool = False

    def __post_init__(self) -> None:
        self.samples = deque(maxlen=self.history_size)

    def add_sample(self, sample: MotionSample) -> None:
        self.samples.append(sample)
        self.last_seen_timestamp_ms = sample.timestamp_ms

    def reset_motion(self) -> None:
        """Drop stale motion history after the hand has been out of view.

        Without this the first sample after a gap is differentiated against a
        stale velocity, which manufactures phantom strikes.
        """

        self.samples.clear()
        self.last_velocity = 0.0
        self.phase = PHASE_READY
        self.stroke_peak_velocity = 0.0
        self.descent_max_y = None
        self.ascent_min_y = None
        self.lift_seen = False


class HandStateStore:
    def __init__(self, history_size: int, gap_reset_ms: int = 200) -> None:
        self._history_size = history_size
        self._gap_reset_ms = max(int(gap_reset_ms), 0)
        self._states: dict[int, HandState] = {}

    def get_or_create(self, hand_id: int, handedness: str, timestamp_ms: int | None = None) -> HandState:
        state = self._states.get(hand_id)
        if state is None:
            state = HandState(hand_id=hand_id, handedness=handedness, history_size=self._history_size)
            self._states[hand_id] = state
            return state

        state.handedness = handedness
        if (
            timestamp_ms is not None
            and state.last_seen_timestamp_ms >= 0
            and timestamp_ms - state.last_seen_timestamp_ms > self._gap_reset_ms
        ):
            state.reset_motion()
        return state

    def prune_stale(self, current_timestamp_ms: int, stale_after_ms: int = 1500) -> None:
        stale_ids = [
            hid for hid, s in self._states.items()
            if s.last_seen_timestamp_ms >= 0
            and current_timestamp_ms - s.last_seen_timestamp_ms > stale_after_ms
        ]
        for hid in stale_ids:
            del self._states[hid]


# ── Strike plane estimation ──────────────────────────────────────────

class StrikePlaneEstimator:
    """Learn where strokes actually bottom out, per hand and globally.

    There is no physical drum head in front of the camera, so the strike plane
    is wherever the player keeps turning their hand around. Tracking that as an
    EMA lets the detector self-calibrate instead of relying on a hard-coded
    screen height, and the shared global estimate lets a newly-seen second hand
    start predicting immediately.
    """

    def __init__(self, alpha: float = 0.25, initial: float | None = None, min_observations: int = 2) -> None:
        self._alpha = min(max(float(alpha), 0.01), 1.0)
        self._min_observations = max(int(min_observations), 1)
        self._global: float | None = initial
        self._global_count = self._min_observations if initial is not None else 0
        self._global_top: float | None = None

    @property
    def global_plane(self) -> float | None:
        return self._global if self._global_count >= self._min_observations else None

    def observe(self, hand_state: HandState, turnaround_y: float) -> None:
        y = min(max(float(turnaround_y), 0.0), 1.0)
        if hand_state.strike_plane is None:
            hand_state.strike_plane = y
        else:
            hand_state.strike_plane += self._alpha * (y - hand_state.strike_plane)

        if self._global is None:
            self._global = y
        else:
            self._global += self._alpha * (y - self._global)
        self._global_count += 1

    def observe_top(self, hand_state: HandState, turnaround_y: float) -> None:
        """Record where the lift-off phase of a stroke tops out."""

        y = min(max(float(turnaround_y), 0.0), 1.0)
        if hand_state.stroke_top is None:
            hand_state.stroke_top = y
        else:
            hand_state.stroke_top += self._alpha * (y - hand_state.stroke_top)

        if self._global_top is None:
            self._global_top = y
        else:
            self._global_top += self._alpha * (y - self._global_top)

    def plane_for(self, hand_state: HandState) -> float | None:
        if hand_state.strike_plane is not None:
            return hand_state.strike_plane
        return self.global_plane

    def top_for(self, hand_state: HandState) -> float | None:
        if hand_state.stroke_top is not None:
            return hand_state.stroke_top
        return self._global_top


# ── Hit detection ────────────────────────────────────────────────────

@dataclass(frozen=True)
class HitEvent:
    hand_id: int
    handedness: str
    x: float
    y: float
    velocity: float
    timestamp_ms: int
    predicted_impact_ms: int = -1
    lead_ms: int = 0


def strike_point(
    landmarks: Sequence[tuple[float, float, float]],
    mode: str = "palm_centroid",
    landmark_index: int = DEFAULT_STRIKE_LANDMARK,
) -> tuple[float, float]:
    """Reduce a hand's landmarks to the point whose motion defines a strike."""

    if not landmarks:
        raise ValueError("landmarks must not be empty")

    if mode == "palm_centroid":
        usable = [landmarks[i] for i in PALM_LANDMARK_INDICES if i < len(landmarks)]
        if usable:
            return (
                sum(p[0] for p in usable) / len(usable),
                sum(p[1] for p in usable) / len(usable),
            )

    idx = landmark_index if len(landmarks) > landmark_index else 0
    x, y, _ = landmarks[idx]
    return x, y


class HitDetector:
    """Legacy detector: fires on a two-point downward velocity threshold crossing."""

    _STRIKE_LANDMARK_INDEX = DEFAULT_STRIKE_LANDMARK

    def __init__(self, min_travel: float, velocity_threshold: float, cooldown_ms: int, velocity_cap: float) -> None:
        self._min_travel = min_travel
        self._velocity_threshold = velocity_threshold
        self._cooldown_ms = cooldown_ms
        self._velocity_cap = velocity_cap

    def update(self, hand_state: HandState, landmarks: Sequence[tuple[float, float, float]], timestamp_ms: int) -> HitEvent | None:
        if not landmarks:
            return None

        x, y = self._strike_point(landmarks)
        current = MotionSample(timestamp_ms=timestamp_ms, x=x, y=y)
        hand_state.add_sample(current)

        if len(hand_state.samples) < 2:
            return None

        prev = hand_state.samples[-2]
        dt = (current.timestamp_ms - prev.timestamp_ms) / 1000.0
        if dt <= 0:
            return None

        prior_vel = hand_state.last_velocity
        cur_vel = (current.y - prev.y) / dt
        hand_state.last_velocity = cur_vel

        if not (prior_vel < self._velocity_threshold <= cur_vel):
            return None
        y_vals = [s.y for s in hand_state.samples]
        if (max(y_vals) - min(y_vals)) < self._min_travel:
            return None
        if hand_state.last_hit_timestamp_ms >= 0 and (timestamp_ms - hand_state.last_hit_timestamp_ms) < self._cooldown_ms:
            return None

        hand_state.last_hit_timestamp_ms = timestamp_ms
        return HitEvent(
            hand_id=hand_state.hand_id, handedness=hand_state.handedness,
            x=x, y=y,
            velocity=min(max(cur_vel / self._velocity_cap, 0.0), 1.0),
            timestamp_ms=timestamp_ms,
        )

    def _strike_point(self, landmarks: Sequence[tuple[float, float, float]]) -> tuple[float, float]:
        idx = self._STRIKE_LANDMARK_INDEX if len(landmarks) > self._STRIKE_LANDMARK_INDEX else 0
        x, y, _ = landmarks[idx]
        return x, y


class StrikeDetector:
    """Predictive time-to-contact strike detector.

    Per hand the detector runs a three-phase machine:

    ``READY``  waiting for a downstroke to begin.
    ``ARMED``  descending; tracking peak velocity and extrapolating to impact.
    ``FIRED``  note sent; the hand must physically lift before it can strike
               again. This re-arm requirement, rather than a blind cooldown, is
               what removes double hits: jitter around the trigger point cannot
               re-fire because it never lifts the hand.

    The note is emitted when predicted impact is ``latency_compensation_ms``
    away, so the sound lands on time despite the downstream pipeline delay.
    """

    def __init__(
        self,
        latency_compensation_ms: int = 90,
        arm_velocity: float = 0.45,
        disarm_velocity: float = 0.10,
        fallback_velocity: float = 1.0,
        min_travel: float = 0.035,
        rearm_travel: float = 0.018,
        refractory_ms: int = 55,
        velocity_cap: float = 2.5,
        max_lookahead_ms: int = 260,
        fit_window: int = 5,
        landmark_mode: str = "palm_centroid",
        landmark_index: int = DEFAULT_STRIKE_LANDMARK,
        plane_estimator: StrikePlaneEstimator | None = None,
        use_acceleration: bool = True,
    ) -> None:
        self._latency_s = max(int(latency_compensation_ms), 0) / 1000.0
        self._arm_velocity = float(arm_velocity)
        self._disarm_velocity = float(disarm_velocity)
        self._fallback_velocity = float(fallback_velocity)
        self._min_travel = float(min_travel)
        self._rearm_travel = float(rearm_travel)
        self._refractory_ms = max(int(refractory_ms), 0)
        self._velocity_cap = max(float(velocity_cap), 1e-6)
        self._max_lookahead_s = max(int(max_lookahead_ms), 0) / 1000.0
        self._fit_window = max(int(fit_window), 2)
        self._landmark_mode = landmark_mode
        self._landmark_index = landmark_index
        self._planes = plane_estimator if plane_estimator is not None else StrikePlaneEstimator()
        self._use_acceleration = use_acceleration

    @property
    def plane_estimator(self) -> StrikePlaneEstimator:
        return self._planes

    def update(
        self,
        hand_state: HandState,
        landmarks: Sequence[tuple[float, float, float]],
        timestamp_ms: int,
    ) -> HitEvent | None:
        if not landmarks:
            return None

        x, y = strike_point(landmarks, mode=self._landmark_mode, landmark_index=self._landmark_index)
        hand_state.add_sample(MotionSample(timestamp_ms=timestamp_ms, x=x, y=y))

        window = select_fit_window(hand_state.samples, self._fit_window)
        kin = fit_kinematics(window)
        if kin is None:
            return None

        previous_velocity = hand_state.last_velocity
        hand_state.last_velocity = kin.vy

        # A turnaround marks where this player's strokes actually bottom out.
        # Record the deepest point reached during the descent rather than the
        # sample that happened to be newest when the fitted velocity flipped
        # sign, which lags the true turnaround by most of the fit window.
        if kin.vy > 0.0:
            hand_state.descent_max_y = max(hand_state.descent_max_y if hand_state.descent_max_y is not None else y, y)
            if previous_velocity < 0.0 and hand_state.ascent_min_y is not None:
                self._planes.observe_top(hand_state, hand_state.ascent_min_y)
                hand_state.ascent_min_y = None
        else:
            if kin.vy <= -self._disarm_velocity:
                hand_state.lift_seen = True
            hand_state.ascent_min_y = min(hand_state.ascent_min_y if hand_state.ascent_min_y is not None else y, y)
            if previous_velocity > 0.0 and hand_state.descent_max_y is not None:
                self._planes.observe(hand_state, hand_state.descent_max_y)
                hand_state.descent_max_y = None

        if hand_state.phase == PHASE_FIRED:
            # Test the lift against the fitted position, not the raw sample:
            # landmark noise alone can fake a lift large enough to re-arm and
            # let the same stroke fire twice.
            self._maybe_rearm(hand_state, kin, kin.y, timestamp_ms)
            return None

        if hand_state.phase == PHASE_READY:
            if kin.vy < self._arm_velocity:
                return None
            if not hand_state.lift_seen:
                # A drum stroke is preceded by a lift. A hand that has only ever
                # travelled downwards is being lowered, not played -- and if it
                # has never struck it is borrowing the other hand's strike
                # plane, so without this it would fire on the way down to rest.
                return None
            hand_state.phase = PHASE_ARMED
            # Measure the stroke from where it actually began, not from wherever
            # the hand happened to be when velocity crossed the arm threshold.
            # On a fast stroke the threshold is not crossed until well into the
            # descent, and charging that distance against the travel gate costs
            # a frame of lead on exactly the strokes that can least afford it.
            top = self._planes.top_for(hand_state)
            candidates = [y]
            if hand_state.ascent_min_y is not None:
                candidates.append(hand_state.ascent_min_y)
            if top is not None:
                candidates.append(top)
            hand_state.stroke_start_y = min(candidates)
            hand_state.stroke_peak_velocity = kin.vy
            # Fall through: a stroke fast enough to arm may already be due.

        # ARMED
        hand_state.stroke_peak_velocity = max(hand_state.stroke_peak_velocity, kin.vy)

        if kin.vy < self._disarm_velocity:
            # Stroke aborted before reaching the plane.
            hand_state.phase = PHASE_READY
            hand_state.stroke_peak_velocity = 0.0
            return None

        if (y - hand_state.stroke_start_y) < self._min_travel:
            return None

        # Never commit a hit off a two-point finite difference: that estimate is
        # exactly the noise-amplifying case the fitted window exists to avoid.
        # Arming on it is fine, firing on it is not.
        if len(window) < 3:
            return None

        if hand_state.last_hit_timestamp_ms >= 0 and (timestamp_ms - hand_state.last_hit_timestamp_ms) < self._refractory_ms:
            return None

        ttc = self._time_to_contact(hand_state, kin)
        if ttc is None:
            return None
        if ttc > self._latency_s:
            return None

        return self._fire(hand_state, kin, x, y, ttc, timestamp_ms)

    def _time_to_contact(self, hand_state: HandState, kin: Kinematics) -> float | None:
        """Seconds until predicted impact, or None when we should not fire yet."""

        plane = self._planes.plane_for(hand_state)
        if plane is None:
            # No learned plane yet: fall back to a velocity threshold so the
            # very first strokes still play (and teach the estimator a plane).
            return 0.0 if kin.vy >= self._fallback_velocity else None

        top = self._planes.top_for(hand_state)
        ttc: float | None = None
        if top is not None and plane - top > 1e-3:
            ttc = time_to_impact_harmonic(kin.y, kin.vy, top, plane)
            if ttc is not None and self._use_acceleration:
                # Deceleration into the turnaround can only bring impact sooner.
                stopping = time_to_turnaround(kin.vy, kin.ay)
                if stopping is not None:
                    ttc = min(ttc, stopping)

        if ttc is None:
            ttc = time_to_impact(kin.y, kin.vy, kin.ay, plane, use_acceleration=self._use_acceleration)
        if ttc is None:
            return None
        if ttc > self._max_lookahead_s:
            return None
        return ttc

    def _fire(
        self,
        hand_state: HandState,
        kin: Kinematics,
        x: float,
        y: float,
        ttc: float,
        timestamp_ms: int,
    ) -> HitEvent:
        hand_state.phase = PHASE_FIRED
        hand_state.last_hit_timestamp_ms = timestamp_ms
        hand_state.fired_y = y

        # Report the strike where it is predicted to land, not where the hand
        # was when we decided to fire; zone mapping happens at impact.
        predicted_x = min(max(x + kin.vx * ttc, 0.0), 1.0)
        peak = max(hand_state.stroke_peak_velocity, kin.vy)
        hand_state.stroke_peak_velocity = 0.0

        return HitEvent(
            hand_id=hand_state.hand_id,
            handedness=hand_state.handedness,
            x=predicted_x,
            y=y,
            velocity=min(max(peak / self._velocity_cap, 0.0), 1.0),
            timestamp_ms=timestamp_ms,
            predicted_impact_ms=timestamp_ms + int(round(ttc * 1000.0)),
            lead_ms=int(round(ttc * 1000.0)),
        )

    def _maybe_rearm(self, hand_state: HandState, kin: Kinematics, y: float, timestamp_ms: int) -> None:
        if (timestamp_ms - hand_state.last_hit_timestamp_ms) < self._refractory_ms:
            return
        lifted = (hand_state.fired_y - y) >= self._rearm_travel
        rising = kin.vy <= -self._disarm_velocity
        if lifted or rising:
            hand_state.phase = PHASE_READY
            hand_state.stroke_peak_velocity = 0.0


class ZoneHitGate:
    """Apply a short cooldown per zone to suppress near-duplicate hits."""

    def __init__(self, cooldown_ms: int) -> None:
        self._cooldown_ms = max(int(cooldown_ms), 0)
        self._last_hit_ms_by_zone: dict[str, int] = {}

    def should_emit(self, zone: str, timestamp_ms: int) -> bool:
        if self._cooldown_ms == 0:
            return True
        prior = self._last_hit_ms_by_zone.get(zone)
        if prior is not None and (timestamp_ms - prior) < self._cooldown_ms:
            return False
        self._last_hit_ms_by_zone[zone] = timestamp_ms
        return True


# ── Zone mapping ─────────────────────────────────────────────────────

class ZoneMapper:
    def __init__(self, zone_edges: Sequence[float], zone_labels: Sequence[str] = ("SNARE", "TOM")) -> None:
        if len(zone_labels) != len(zone_edges) + 1:
            raise ValueError("zone_labels must contain exactly len(zone_edges) + 1 items")
        if any(e <= 0.0 or e >= 1.0 for e in zone_edges):
            raise ValueError("zone_edges must be within (0, 1)")
        if any(a >= b for a, b in zip(zone_edges, zone_edges[1:])):
            raise ValueError("zone_edges must be strictly increasing")
        self._zone_edges = tuple(zone_edges)
        self._zone_labels = tuple(zone_labels)

    def zone_for_x(self, x: float) -> str:
        clamped = min(max(x, 0.0), 1.0)
        for i, edge in enumerate(self._zone_edges):
            if clamped < edge:
                return self._zone_labels[i]
        return self._zone_labels[-1]


# ── Gesture routing ──────────────────────────────────────────────────

@dataclass(frozen=True)
class CommandEvent:
    command: str
    label: str
    handedness: str
    timestamp_ms: int


class GestureRouter:
    def __init__(self, label_to_command: Mapping[str, str], cooldown_ms: int = 900) -> None:
        self._label_to_command = dict(label_to_command)
        self._cooldown_ms = cooldown_ms
        self._last_emitted_ms: dict[tuple[str, str], int] = {}

    def route(self, label: str | None, handedness: str, timestamp_ms: int) -> CommandEvent | None:
        if not label:
            return None
        command = self._label_to_command.get(label)
        if command is None:
            return None
        key = (command, handedness)
        prior = self._last_emitted_ms.get(key)
        if prior is not None and (timestamp_ms - prior) < self._cooldown_ms:
            return None
        self._last_emitted_ms[key] = timestamp_ms
        return CommandEvent(command=command, label=label, handedness=handedness, timestamp_ms=timestamp_ms)
