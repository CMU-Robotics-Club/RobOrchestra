"""Tests for groove and fill generation."""

from __future__ import annotations

from jam.beat_tracker import BeatEvent
from jam.groove_engine import GrooveEngine


def _beat(timestamp_s: float, beat_in_bar: int, bar_index: int, bpm: float = 120.0) -> BeatEvent:
    period = 60.0 / bpm
    return BeatEvent(timestamp_s=timestamp_s, bpm=bpm, period_s=period, beat_in_bar=beat_in_bar, bar_index=bar_index)


def test_groove_notes_are_quantized_to_16th_grid() -> None:
    engine = GrooveEngine(intensity=2, mode="groove", fill_every_bars=8, fill_probability=0.30, rng_seed=1)
    beat = _beat(timestamp_s=10.0, beat_in_bar=1, bar_index=0, bpm=120.0)
    notes = engine.notes_for_beat(beat, confidence=0.9)

    for note in notes:
        delta = note.timestamp_s - beat.timestamp_s
        # 16th notes at 120 BPM are 0.125s
        assert abs((delta / 0.125) - round(delta / 0.125)) < 1e-6


def test_fill_appears_on_fill_bar_last_beat() -> None:
    engine = GrooveEngine(intensity=3, mode="groove", fill_every_bars=1, fill_probability=1.0, rng_seed=7)

    # Beat 1 decides whether this bar gets a fill.
    engine.notes_for_beat(_beat(0.0, beat_in_bar=1, bar_index=1), confidence=0.9)
    notes = engine.notes_for_beat(_beat(1.5, beat_in_bar=4, bar_index=1), confidence=0.9)

    assert notes
    assert all(n.source == "fill" for n in notes)


def test_fill_suppressed_when_confidence_is_low() -> None:
    engine = GrooveEngine(intensity=3, mode="busy", fill_every_bars=1, fill_probability=1.0, rng_seed=9)

    engine.notes_for_beat(_beat(0.0, beat_in_bar=1, bar_index=1), confidence=0.3)
    notes = engine.notes_for_beat(_beat(1.5, beat_in_bar=4, bar_index=1), confidence=0.3)

    assert notes
    assert all(n.source == "groove" for n in notes)


def test_force_fill_command_triggers_next_eligible_bar() -> None:
    engine = GrooveEngine(intensity=2, mode="sparse", fill_every_bars=8, fill_probability=0.0, rng_seed=3)
    engine.request_fill()

    engine.notes_for_beat(_beat(0.0, beat_in_bar=1, bar_index=2), confidence=0.95)
    notes = engine.notes_for_beat(_beat(1.5, beat_in_bar=4, bar_index=2), confidence=0.95)

    assert notes
    assert all(n.source == "fill" for n in notes)
