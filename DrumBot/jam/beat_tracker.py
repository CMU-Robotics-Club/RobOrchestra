"""Beat and tempo tracking for jam-along demo."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BeatEvent:
    """One emitted beat pulse from the tracker."""

    timestamp_s: float
    bpm: float
    period_s: float
    beat_in_bar: int
    bar_index: int


@dataclass(frozen=True)
class BeatState:
    """Current beat tracker state."""

    bpm: float | None
    confidence: float
    locked: bool
    beat_in_bar: int
    bar_index: int
    last_onset_s: float | None


class BeatTracker:
    """Realtime beat tracker using spectral flux + IOI voting + simple phase lock."""

    def __init__(self, sample_rate: int, min_bpm: float = 70.0, max_bpm: float = 180.0) -> None:
        self._sample_rate = float(sample_rate)
        self._min_bpm = float(min_bpm)
        self._max_bpm = float(max_bpm)

        self._flux_history: deque[float] = deque(maxlen=128)
        self._onset_times: deque[float] = deque(maxlen=64)
        self._prev_spectrum: np.ndarray | None = None

        self._last_onset_s: float | None = None
        self._last_emitted_beat_s: float | None = None
        self._next_beat_s: float | None = None

        self._bpm: float | None = None
        self._confidence = 0.0
        self._locked = False
        self._beat_counter = 0

        self._refractory_s = 0.12

    def update(self, samples: np.ndarray, timestamp_s: float) -> tuple[BeatState, list[BeatEvent]]:
        timestamp_s = float(timestamp_s)

        flux = self._spectral_flux(samples)
        threshold = self._adaptive_threshold()
        onset_detected = self._is_onset(flux=flux, threshold=threshold, timestamp_s=timestamp_s)
        self._flux_history.append(flux)

        if onset_detected:
            self._onset_times.append(timestamp_s)
            self._last_onset_s = timestamp_s
            self._update_tempo_estimate()
            self._update_phase_from_onset(timestamp_s)
        else:
            self._decay_confidence_if_stale(timestamp_s)

        beat_events = self._emit_due_beats(timestamp_s)

        next_beat_in_bar = (self._beat_counter % 4) + 1
        next_bar_index = self._beat_counter // 4
        state = BeatState(
            bpm=self._bpm,
            confidence=self._confidence,
            locked=self._locked,
            beat_in_bar=next_beat_in_bar,
            bar_index=next_bar_index,
            last_onset_s=self._last_onset_s,
        )
        return state, beat_events

    def _spectral_flux(self, samples: np.ndarray) -> float:
        mono = np.asarray(samples, dtype=np.float32)
        if mono.size == 0:
            return 0.0

        window = np.hanning(mono.size).astype(np.float32)
        spectrum = np.abs(np.fft.rfft(mono * window)).astype(np.float32)

        if self._prev_spectrum is None:
            self._prev_spectrum = spectrum
            return 0.0

        flux = float(np.sum(np.maximum(spectrum - self._prev_spectrum, 0.0)))
        self._prev_spectrum = spectrum
        return float(np.log1p(max(flux, 0.0)))

    def _adaptive_threshold(self) -> float:
        if len(self._flux_history) < 12:
            return float("inf")
        values = np.asarray(self._flux_history, dtype=np.float32)
        median = float(np.median(values))
        mad = float(np.median(np.abs(values - median)))
        floor = max(0.04, median * 0.65)
        return floor + 3.0 * max(mad, 0.002)

    def _is_onset(self, flux: float, threshold: float, timestamp_s: float) -> bool:
        if flux <= threshold:
            return False
        if self._last_onset_s is None:
            return True
        return (timestamp_s - self._last_onset_s) >= self._refractory_s

    def _update_tempo_estimate(self) -> None:
        if len(self._onset_times) < 3:
            return

        intervals = np.diff(np.asarray(self._onset_times, dtype=np.float64))
        if intervals.size > 16:
            intervals = intervals[-16:]
        valid_intervals = [
            float(i)
            for i in intervals
            if 0.20 <= i <= 1.20
        ]
        if not valid_intervals:
            return

        bpms: list[float] = []
        for ioi in valid_intervals:
            bpm = 60.0 / ioi
            while bpm < self._min_bpm:
                bpm *= 2.0
            while bpm > self._max_bpm:
                bpm /= 2.0
            if self._min_bpm <= bpm <= self._max_bpm:
                bpms.append(bpm)

        if not bpms:
            return

        candidate = float(np.median(np.asarray(bpms, dtype=np.float64)))

        if self._bpm is None:
            self._bpm = candidate
        else:
            alpha = 0.35 if not self._locked else 0.12
            self._bpm = (1.0 - alpha) * self._bpm + alpha * candidate

        close_count = sum(1 for bpm in bpms if abs(bpm - candidate) <= 6.0)
        consistency = close_count / max(len(bpms), 1)
        sample_strength = min(1.0, len(bpms) / 8.0)
        self._confidence = max(0.0, min(1.0, consistency * sample_strength))

        self._locked = self._confidence >= 0.55 and len(bpms) >= 4 and self._bpm is not None
        if self._locked and self._next_beat_s is None and self._last_onset_s is not None:
            self._next_beat_s = self._last_onset_s

    def _update_phase_from_onset(self, onset_s: float) -> None:
        if not self._locked or self._bpm is None:
            return

        period = 60.0 / self._bpm
        if self._next_beat_s is None:
            self._next_beat_s = onset_s
            return

        nearest_index = int(round((onset_s - self._next_beat_s) / period))
        nearest_time = self._next_beat_s + nearest_index * period
        phase_error = onset_s - nearest_time

        if abs(phase_error) > 0.40 * period:
            nearest_time = onset_s
            phase_error = 0.0

        corrected = nearest_time + (phase_error * 0.30)
        if self._last_emitted_beat_s is not None:
            while corrected <= self._last_emitted_beat_s:
                corrected += period

        self._next_beat_s = corrected

    def _decay_confidence_if_stale(self, timestamp_s: float) -> None:
        if self._last_onset_s is None:
            self._confidence *= 0.98
            return

        silence_s = timestamp_s - self._last_onset_s
        if silence_s > 1.5:
            self._confidence *= 0.95
        if silence_s > 3.0:
            self._locked = False
            self._next_beat_s = None

    def _emit_due_beats(self, timestamp_s: float) -> list[BeatEvent]:
        if not self._locked or self._bpm is None or self._next_beat_s is None:
            return []

        period = 60.0 / self._bpm
        events: list[BeatEvent] = []

        while self._next_beat_s <= timestamp_s + 1e-6:
            beat_in_bar = (self._beat_counter % 4) + 1
            bar_index = self._beat_counter // 4
            events.append(
                BeatEvent(
                    timestamp_s=self._next_beat_s,
                    bpm=self._bpm,
                    period_s=period,
                    beat_in_bar=beat_in_bar,
                    bar_index=bar_index,
                )
            )
            self._last_emitted_beat_s = self._next_beat_s
            self._beat_counter += 1
            self._next_beat_s += period

        return events
