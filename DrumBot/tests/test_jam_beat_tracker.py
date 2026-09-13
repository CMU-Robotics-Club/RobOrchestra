"""Tests for realtime beat tracking."""

from __future__ import annotations

import numpy as np

from jam.beat_tracker import BeatTracker


def _pulse_times(segments: list[tuple[float, int]], start_s: float = 0.5) -> list[float]:
    times: list[float] = []
    t = start_s
    for bpm, beats in segments:
        period = 60.0 / bpm
        for _ in range(beats):
            times.append(t)
            t += period
    return times


def _run_tracker(pulse_times: list[float], sample_rate: int = 48_000, block_size: int = 512) -> tuple[float | None, float, bool]:
    tracker = BeatTracker(sample_rate=sample_rate, min_bpm=70.0, max_bpm=180.0)

    duration_s = (pulse_times[-1] + 1.0) if pulse_times else 8.0
    n_blocks = int(duration_s * sample_rate / block_size)

    pulse_idx = 0
    state_bpm: float | None = None
    state_conf = 0.0
    state_locked = False

    for block in range(n_blocks):
        t_start = block * block_size / sample_rate
        t_end = (block + 1) * block_size / sample_rate
        samples = np.zeros(block_size, dtype=np.float32)

        while pulse_idx < len(pulse_times) and pulse_times[pulse_idx] <= t_end:
            pulse_t = pulse_times[pulse_idx]
            if pulse_t >= t_start:
                offset = int((pulse_t - t_start) * sample_rate)
                offset = max(0, min(block_size - 1, offset))
                samples[offset] = 1.0
            pulse_idx += 1

        state, _ = tracker.update(samples, t_end)
        state_bpm = state.bpm
        state_conf = state.confidence
        state_locked = state.locked

    return state_bpm, state_conf, state_locked


def test_tracker_converges_for_120_bpm_click_track() -> None:
    pulses = _pulse_times([(120.0, 24)])
    bpm, conf, locked = _run_tracker(pulses)
    assert bpm is not None
    assert abs(bpm - 120.0) <= 3.0
    assert locked is True
    assert conf >= 0.55


def test_tracker_relocks_after_tempo_change() -> None:
    pulses = _pulse_times([(100.0, 16), (130.0, 20)])
    bpm, conf, locked = _run_tracker(pulses)
    assert bpm is not None
    assert abs(bpm - 130.0) <= 6.0
    assert locked is True
    assert conf >= 0.50


def test_tracker_stays_unlocked_on_noise_only() -> None:
    sample_rate = 48_000
    block_size = 512
    tracker = BeatTracker(sample_rate=sample_rate, min_bpm=70.0, max_bpm=180.0)

    rng = np.random.default_rng(123)
    n_blocks = int(10.0 * sample_rate / block_size)
    state_conf = 0.0
    state_locked = False

    for block in range(n_blocks):
        t_end = (block + 1) * block_size / sample_rate
        samples = (rng.normal(0.0, 0.002, size=block_size)).astype(np.float32)
        state, _ = tracker.update(samples, t_end)
        state_conf = state.confidence
        state_locked = state.locked

    assert state_locked is False
    assert state_conf < 0.55
