"""Air-drum hit detection using hand landmark motion history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from tracking.hand_state import HandState, MotionSample


@dataclass(frozen=True)
class HitEvent:
    """Detected hit event with normalized strike position and velocity."""

    hand_id: int
    handedness: str
    x: float
    y: float
    velocity: float
    timestamp_ms: int


class HitDetector:
    """Detects downward strike motions from recent hand motion samples."""

    _STRIKE_LANDMARK_INDEX = 9

    def __init__(
        self,
        min_travel: float,
        velocity_threshold: float,
        cooldown_ms: int,
        velocity_cap: float,
    ) -> None:
        self._min_travel = min_travel
        self._velocity_threshold = velocity_threshold
        self._cooldown_ms = cooldown_ms
        self._velocity_cap = velocity_cap

    def update(
        self,
        hand_state: HandState,
        landmarks: Sequence[tuple[float, float, float]],
        timestamp_ms: int,
    ) -> HitEvent | None:
        """Update one hand and return a hit event if a strike is detected."""

        if not landmarks:
            return None

        x, y = self._strike_point(landmarks)
        current_sample = MotionSample(timestamp_ms=timestamp_ms, x=x, y=y)
        hand_state.add_sample(current_sample)

        if len(hand_state.samples) < 2:
            return None

        previous_sample = hand_state.samples[-2]
        delta_t_sec = (current_sample.timestamp_ms - previous_sample.timestamp_ms) / 1000.0
        if delta_t_sec <= 0:
            return None

        prior_velocity = hand_state.last_velocity
        current_velocity = (current_sample.y - previous_sample.y) / delta_t_sec
        hand_state.last_velocity = current_velocity

        if not self._is_strike_crossing(prior_velocity, current_velocity):
            return None
        if not self._has_sufficient_travel(hand_state):
            return None
        if not self._cooldown_elapsed(hand_state, timestamp_ms):
            return None

        hand_state.last_hit_timestamp_ms = timestamp_ms
        return HitEvent(
            hand_id=hand_state.hand_id,
            handedness=hand_state.handedness,
            x=x,
            y=y,
            velocity=min(max(current_velocity / self._velocity_cap, 0.0), 1.0),
            timestamp_ms=timestamp_ms,
        )

    def _is_strike_crossing(self, prior_velocity: float, current_velocity: float) -> bool:
        """Treat a hit as the moment downward speed crosses the threshold."""

        return prior_velocity < self._velocity_threshold <= current_velocity

    def _has_sufficient_travel(self, hand_state: HandState) -> bool:
        """Check whether y-travel in recent samples is large enough to count as a hit."""

        y_positions = [sample.y for sample in hand_state.samples]
        return (max(y_positions) - min(y_positions)) >= self._min_travel

    def _cooldown_elapsed(self, hand_state: HandState, timestamp_ms: int) -> bool:
        """Apply a per-hand minimum interval between emitted hits."""

        if hand_state.last_hit_timestamp_ms < 0:
            return True
        return (timestamp_ms - hand_state.last_hit_timestamp_ms) >= self._cooldown_ms

    def _strike_point(self, landmarks: Sequence[tuple[float, float, float]]) -> tuple[float, float]:
        """Use middle MCP as strike proxy; fallback to wrist when unavailable."""

        index = self._STRIKE_LANDMARK_INDEX if len(landmarks) > self._STRIKE_LANDMARK_INDEX else 0
        x, y, _ = landmarks[index]
        return x, y
