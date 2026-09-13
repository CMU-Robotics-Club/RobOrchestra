"""End-to-end tests for the main.py processing path (no camera, no MIDI hardware)."""

from __future__ import annotations

import math
from collections import deque

import pytest

import main
from config import AppConfig
from main import EventDispatcher, LatencyMonitor, _build_detector, _process_observation
from tracking import GestureRouter, HandStateStore, ZoneHitGate, ZoneMapper
from vision import FrameObservation, HandObservation


class FakeSerial:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def send_line(self, line: str) -> None:
        self.lines.append(line)


class FakeMidi:
    def __init__(self) -> None:
        self.notes: list[tuple[int, float]] = []
        self.ccs: list[tuple[int, int]] = []

    def send_note_on(self, note: int, velocity_normalized: float) -> int:
        self.notes.append((note, velocity_normalized))
        return 1

    def send_note_off(self, note: int) -> int:
        return 1

    def send_control_change(self, control: int, value: int) -> int:
        self.ccs.append((control, value))
        return 1


def _harness(config: AppConfig):
    serial, midi = FakeSerial(), FakeMidi()
    dispatcher = EventDispatcher(
        serial_client=serial,
        midi_client=midi,
        midi_zone_notes={"SNARE": 38, "TOM": 45},
        midi_note_off_enabled=False,
        midi_command_cc=dict(config.midi_command_cc),
        midi_command_value=config.midi_command_value,
        recent_commands=deque(maxlen=5),
        recent_hits=deque(maxlen=5),
    )
    ctx = dict(
        config=config,
        hand_states=HandStateStore(history_size=config.hit_history_size, gap_reset_ms=config.hand_gap_reset_ms),
        detector=_build_detector(config),
        zone_hit_gate=ZoneHitGate(cooldown_ms=config.hit_zone_cooldown_ms),
        zone_mapper=ZoneMapper(zone_edges=(0.5,), zone_labels=("SNARE", "TOM")),
        gesture_router=GestureRouter(label_to_command=config.gesture_to_command, cooldown_ms=config.gesture_command_cooldown_ms),
        dispatcher=dispatcher,
        monitor=LatencyMonitor(),
    )
    return serial, midi, ctx


def _observation(timestamp_ms: int, hands: list[tuple[str, float, float, str | None]]) -> FrameObservation:
    return FrameObservation(
        timestamp_ms=timestamp_ms,
        hands=tuple(
            HandObservation(
                hand_id=i,
                handedness=handed,
                landmarks=tuple((x, y, 0.0) for _ in range(21)),
                top_gesture=gesture,
                top_gesture_score=0.9 if gesture else 0.0,
            )
            for i, (handed, x, y, gesture) in enumerate(hands)
        ),
    )


def _drum(ctx, x: float, handed: str, strokes: int, start_ms: int = 0, fps: int = 60,
          top: float = 0.28, bottom: float = 0.66, period_ms: int = 340) -> int:
    """Play a run of smooth strokes at one x position."""

    dt = 1000 // fps
    t = start_ms
    mid, amp = (top + bottom) / 2.0, (bottom - top) / 2.0
    # Start at the bottom of the swing so the hand lifts before its first
    # strike, as a player does; a cold descent is treated as lowering to rest.
    while t < start_ms + strokes * period_ms:
        phase = 0.5 + ((t - start_ms) % period_ms) / period_ms
        y = mid - amp * math.cos(2.0 * math.pi * phase)
        _process_observation(observation=_observation(t, [(handed, x, y, None)]), **ctx)
        t += dt
    return t


def test_strokes_produce_one_midi_note_each() -> None:
    serial, midi, ctx = _harness(AppConfig())
    _drum(ctx, x=0.25, handed="Left", strokes=6)
    assert len(midi.notes) == 6, f"expected 6 notes, got {len(midi.notes)}"


def test_left_and_right_zones_route_to_different_notes() -> None:
    _, midi, ctx = _harness(AppConfig())
    t = _drum(ctx, x=0.20, handed="Left", strokes=4)
    _drum(ctx, x=0.80, handed="Right", strokes=4, start_ms=t + 500)

    played = [note for note, _ in midi.notes]
    assert 38 in played and 45 in played
    assert played[:4] == [38, 38, 38, 38]
    assert played[-4:] == [45, 45, 45, 45]


def test_serial_and_midi_stay_in_lockstep() -> None:
    serial, midi, ctx = _harness(AppConfig())
    _drum(ctx, x=0.25, handed="Left", strokes=5)
    hit_lines = [line for line in serial.lines if line.startswith("HIT,")]
    assert len(hit_lines) == len(midi.notes)
    assert all(line.startswith("HIT,SNARE,") for line in hit_lines)


def test_still_hand_produces_no_notes() -> None:
    _, midi, ctx = _harness(AppConfig())
    for i in range(120):
        y = 0.45 + (0.003 if i % 2 else -0.003)
        _process_observation(observation=_observation(i * 16, [("Left", 0.3, y, None)]), **ctx)
    assert midi.notes == []


def test_gesture_emits_command_cc() -> None:
    _, midi, ctx = _harness(AppConfig())
    _process_observation(observation=_observation(0, [("Left", 0.3, 0.4, "Open_Palm")]), **ctx)
    assert (20, 127) in midi.ccs


def test_two_hands_are_tracked_independently() -> None:
    _, midi, ctx = _harness(AppConfig())
    mid, amp, period = 0.47, 0.19, 340
    t = 0
    while t < 5 * period:
        # Right hand runs half a period out of phase with the left.
        pl = (t % period) / period
        pr = ((t + period // 2) % period) / period
        yl = mid - amp * math.cos(2.0 * math.pi * pl)
        yr = mid - amp * math.cos(2.0 * math.pi * pr)
        _process_observation(
            observation=_observation(t, [("Left", 0.22, yl, None), ("Right", 0.78, yr, None)]),
            **ctx,
        )
        t += 16

    played = [note for note, _ in midi.notes]
    assert played.count(38) >= 4, f"left hand under-triggered: {played}"
    assert played.count(45) >= 4, f"right hand under-triggered: {played}"


def test_legacy_detector_still_runs_through_the_pipeline() -> None:
    _, midi, ctx = _harness(AppConfig(detector="legacy"))
    _drum(ctx, x=0.25, handed="Left", strokes=6)
    assert len(midi.notes) > 0


def test_velocity_is_within_midi_range() -> None:
    _, midi, ctx = _harness(AppConfig())
    _drum(ctx, x=0.25, handed="Left", strokes=5)
    assert midi.notes
    for _, velocity in midi.notes:
        assert 0.0 <= velocity <= 1.0


# ── Zone / note resolution helpers ───────────────────────────────────

def test_zone_labels_inferred_from_bot_port_names() -> None:
    labels = main._resolve_zone_labels(("SNARE", "TOM"), ("RobOrchestra_Snare", "RobOrchestra_Tom"))
    assert labels == ("SNARE", "TOM")


def test_zone_labels_fall_back_when_no_ports() -> None:
    assert main._resolve_zone_labels(("SNARE", "TOM"), ()) == ("SNARE", "TOM")


def test_duplicate_bot_names_get_distinct_labels() -> None:
    labels = main._resolve_zone_labels(("SNARE",), ("RobOrchestra_Snare", "RobOrchestra_Snare"))
    assert labels == ("SNARE", "SNARE_2")


def test_zone_edges_split_evenly_for_three_bots() -> None:
    edges = main._resolve_zone_edges(("A", "B", "C"), (0.5,))
    assert edges == pytest.approx((1 / 3, 2 / 3))


def test_midi_notes_resolved_for_suffixed_zones() -> None:
    notes = main._resolve_midi_zone_notes(("SNARE", "SNARE_2"), {"SNARE": 38})
    assert notes["SNARE"] == 38
    assert notes["SNARE_2"] == 38


def test_latency_monitor_reports_percentiles() -> None:
    m = LatencyMonitor()
    for i in range(20):
        m.record(captured_at_s=0.0 + i, now_s=0.05 + i)
    summary = m.summary()
    assert "mean=" in summary and "p95=" in summary


def test_latency_monitor_ignores_missing_capture_times() -> None:
    m = LatencyMonitor()
    m.record(captured_at_s=0.0, now_s=1.0)
    assert m.mean_ms == 0.0
