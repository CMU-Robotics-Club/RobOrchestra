"""Tests for tracking module: zone mapping, hit detection, gesture routing."""

from __future__ import annotations

import pytest

from tracking import GestureRouter, HandState, HitDetector, ZoneMapper


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


# ── Hit detection ────────────────────────────────────────────────────

def _landmarks(x: float, y: float) -> tuple[tuple[float, float, float], ...]:
    return tuple((x, y, 0.0) for _ in range(21))


def test_detects_hit_on_downward_velocity_crossing() -> None:
    d = HitDetector(min_travel=0.03, velocity_threshold=1.0, cooldown_ms=120, velocity_cap=2.5)
    s = HandState(hand_id=0, handedness="Left", history_size=8)
    assert d.update(s, _landmarks(0.40, 0.20), 0) is None
    assert d.update(s, _landmarks(0.40, 0.22), 33) is None
    hit = d.update(s, _landmarks(0.40, 0.30), 66)
    assert hit is not None
    assert hit.handedness == "Left"
    assert 0.0 <= hit.velocity <= 1.0


def test_applies_cooldown_between_hits() -> None:
    d = HitDetector(min_travel=0.03, velocity_threshold=1.0, cooldown_ms=120, velocity_cap=2.5)
    s = HandState(hand_id=1, handedness="Right", history_size=8)
    d.update(s, _landmarks(0.65, 0.20), 0)
    d.update(s, _landmarks(0.65, 0.22), 33)
    assert d.update(s, _landmarks(0.65, 0.30), 66) is not None
    d.update(s, _landmarks(0.65, 0.31), 99)
    assert d.update(s, _landmarks(0.65, 0.40), 132) is None
    d.update(s, _landmarks(0.65, 0.41), 220)
    assert d.update(s, _landmarks(0.65, 0.50), 253) is not None


def test_requires_minimum_travel() -> None:
    d = HitDetector(min_travel=0.05, velocity_threshold=1.0, cooldown_ms=120, velocity_cap=2.5)
    s = HandState(hand_id=2, handedness="Left", history_size=8)
    d.update(s, _landmarks(0.20, 0.20), 0)
    d.update(s, _landmarks(0.20, 0.205), 33)
    assert d.update(s, _landmarks(0.20, 0.24), 66) is None


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
