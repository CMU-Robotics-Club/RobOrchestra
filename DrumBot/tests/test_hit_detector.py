"""Unit tests for strike detection logic."""

from __future__ import annotations

from tracking.hand_state import HandState
from tracking.hit_detector import HitDetector


def _landmarks(x: float, y: float) -> tuple[tuple[float, float, float], ...]:
    points = [(x, y, 0.0) for _ in range(21)]
    return tuple(points)


def test_detects_hit_on_downward_velocity_crossing() -> None:
    detector = HitDetector(
        min_travel=0.03,
        velocity_threshold=1.0,
        cooldown_ms=120,
        velocity_cap=2.5,
    )
    state = HandState(hand_id=0, handedness="Left", history_size=8)

    assert detector.update(state, _landmarks(0.40, 0.20), 0) is None
    assert detector.update(state, _landmarks(0.40, 0.22), 33) is None

    hit = detector.update(state, _landmarks(0.40, 0.30), 66)
    assert hit is not None
    assert hit.handedness == "Left"
    assert hit.hand_id == 0
    assert hit.x == 0.40
    assert 0.0 <= hit.velocity <= 1.0


def test_applies_cooldown_between_hits() -> None:
    detector = HitDetector(
        min_travel=0.03,
        velocity_threshold=1.0,
        cooldown_ms=120,
        velocity_cap=2.5,
    )
    state = HandState(hand_id=1, handedness="Right", history_size=8)

    detector.update(state, _landmarks(0.65, 0.20), 0)
    detector.update(state, _landmarks(0.65, 0.22), 33)
    first_hit = detector.update(state, _landmarks(0.65, 0.30), 66)
    assert first_hit is not None

    detector.update(state, _landmarks(0.65, 0.31), 99)
    blocked_hit = detector.update(state, _landmarks(0.65, 0.40), 132)
    assert blocked_hit is None

    detector.update(state, _landmarks(0.65, 0.41), 220)
    second_hit = detector.update(state, _landmarks(0.65, 0.50), 253)
    assert second_hit is not None


def test_requires_minimum_travel() -> None:
    detector = HitDetector(
        min_travel=0.05,
        velocity_threshold=1.0,
        cooldown_ms=120,
        velocity_cap=2.5,
    )
    state = HandState(hand_id=2, handedness="Left", history_size=8)

    detector.update(state, _landmarks(0.20, 0.20), 0)
    detector.update(state, _landmarks(0.20, 0.205), 33)
    no_hit = detector.update(state, _landmarks(0.20, 0.24), 66)
    assert no_hit is None
