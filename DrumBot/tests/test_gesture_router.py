"""Unit tests for gesture-command routing."""

from __future__ import annotations

from tracking.gesture_router import GestureRouter


def _router() -> GestureRouter:
    return GestureRouter(
        label_to_command={
            "Open_Palm": "ARM",
            "Closed_Fist": "STOP",
        },
        cooldown_ms=500,
    )


def test_routes_known_label_to_command() -> None:
    router = _router()
    event = router.route(label="Open_Palm", handedness="Left", timestamp_ms=1000)
    assert event is not None
    assert event.command == "ARM"


def test_unknown_label_produces_no_command() -> None:
    router = _router()
    assert router.route(label="Victory", handedness="Left", timestamp_ms=1000) is None


def test_cooldown_blocks_repeated_command_for_same_hand() -> None:
    router = _router()
    first = router.route(label="Closed_Fist", handedness="Right", timestamp_ms=1000)
    second = router.route(label="Closed_Fist", handedness="Right", timestamp_ms=1200)
    third = router.route(label="Closed_Fist", handedness="Right", timestamp_ms=1600)
    assert first is not None
    assert second is None
    assert third is not None


def test_cooldown_is_independent_per_handedness() -> None:
    router = _router()
    left = router.route(label="Open_Palm", handedness="Left", timestamp_ms=1000)
    right = router.route(label="Open_Palm", handedness="Right", timestamp_ms=1000)
    assert left is not None
    assert right is not None
