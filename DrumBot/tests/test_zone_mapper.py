"""Unit tests for drum zone mapping."""

from __future__ import annotations

import pytest

from tracking.zone_mapper import ZoneMapper


def test_zone_for_x_boundaries() -> None:
    mapper = ZoneMapper(zone_edges=(0.25, 0.5, 0.75))

    assert mapper.zone_for_x(0.00) == "HIHAT"
    assert mapper.zone_for_x(0.24) == "HIHAT"
    assert mapper.zone_for_x(0.25) == "SNARE"
    assert mapper.zone_for_x(0.50) == "TOM"
    assert mapper.zone_for_x(0.74) == "TOM"
    assert mapper.zone_for_x(0.75) == "CRASH"


def test_zone_for_x_clamps_out_of_range_values() -> None:
    mapper = ZoneMapper(zone_edges=(0.25, 0.5, 0.75))
    assert mapper.zone_for_x(-1.0) == "HIHAT"
    assert mapper.zone_for_x(2.0) == "CRASH"


def test_invalid_zone_edges_raise() -> None:
    with pytest.raises(ValueError):
        ZoneMapper(zone_edges=(0.5, 0.4, 0.8))

    with pytest.raises(ValueError):
        ZoneMapper(zone_edges=(0.2, 0.5, 1.2))
