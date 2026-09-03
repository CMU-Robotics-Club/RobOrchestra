"""Measure how late a bot really is, instead of guessing.

fleet.py says it plainly: mech_latency_ms is the least trustworthy number in
the project, because nobody has measured it. This module is the measuring.
It asks the ensemble to strike a bot at known instants, listens on a
microphone, finds the acoustic onsets, and reports the gap between when a
hit was meant to sound and when it did. That gap, added to whatever the
fleet already compensates, is the number the fleet should carry.

The analysis half — finding onsets in audio and pairing them with intended
hits — is pure numpy and tested on synthesised drum sounds, so the tool is
known to read a clean recording correctly before it meets a room. The
capture half is a thin wrapper around sounddevice that stamps each audio
block on the monotonic clock, corrected by the input latency PortAudio
reports, so onset times land on the same clock the ensemble schedules on.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from statistics import mean, median, pstdev

import numpy as np

HOP = 64                    # samples per energy frame: 1.3 ms at 48 kHz
ABOVE_FLOOR_DB = 10.0       # an onset is this far above the recording's quiet floor
QUIET_DB = 6.0              # and everything just before it was no further than this
QUIET_S = 0.04              # for this long
REFRACTORY_S = 0.25         # a hit plus the room's decay; the probe spaces hits wider
MATCH_EARLY_S = 0.03        # an onset this far *before* the intended time still counts
MATCH_LATE_S = 0.40         # and this far after; beyond it the hit is missed

# A recording is only worth reading if the hits stand well clear of the
# room. A microphone at a drum gives 30-50 dB; a laptop listening to its own
# speakers gives about 10, and reads its own noise as hits.
GOOD_SNR_DB = 20.0
GOOD_PEAK = 0.05


@dataclass(frozen=True)
class LatencyReport:
    """What the microphone said about a run of intended hits."""

    intended: int
    samples_ms: tuple[float, ...]   # acoustic onset minus intended time, per matched hit
    missed: int                     # intended hits with no onset in their window
    spurious: int                   # onsets that belonged to no hit
    peak: float = 0.0               # loudest sample in the recording, 0..1
    snr_db: float = 0.0             # loudest frame over the quiet floor

    @property
    def matched(self) -> int:
        return len(self.samples_ms)

    @property
    def clean(self) -> bool:
        """Whether the recording had enough signal over noise to be believed."""
        return self.snr_db >= GOOD_SNR_DB and self.peak >= GOOD_PEAK

    @property
    def median_ms(self) -> float:
        return median(self.samples_ms) if self.samples_ms else float("nan")

    @property
    def mean_ms(self) -> float:
        return mean(self.samples_ms) if self.samples_ms else float("nan")

    @property
    def stdev_ms(self) -> float:
        return pstdev(self.samples_ms) if len(self.samples_ms) > 1 else 0.0

    @property
    def usable(self) -> bool:
        return self.matched >= 3 and self.matched >= self.intended // 2

    def suggested_mech_latency_ms(self, current_ms: float) -> float:
        """What the fleet should carry: what it compensates now plus what is left over."""
        return current_ms + self.median_ms


def detect_onsets(samples: np.ndarray, sample_rate: int) -> list[float]:
    """Times, in seconds from the start of `samples`, where a hit begins.

    A latency probe guarantees one thing about its recording: silence
    between hits. So an onset is the first short frame that rises well
    above the recording's quiet floor after a stretch that stayed near it —
    energy coming up out of nothing — rather than any sharp jump, which a
    ringing drum in a live room produces several of per hit. The refractory
    covers the hit and the room's decay. The time is refined inside the
    frame to the first sample carrying the new energy.
    """
    mono = np.asarray(samples, dtype=np.float32).reshape(-1)
    quiet_frames = max(1, int(QUIET_S * sample_rate / HOP))
    if mono.size < HOP * (quiet_frames + 2):
        return []
    frames = mono[: (mono.size // HOP) * HOP].reshape(-1, HOP)
    energy_db = 10.0 * np.log10(np.mean(frames * frames, axis=1) + 1e-10)
    floor_db = float(np.percentile(energy_db, 20))
    threshold = floor_db + ABOVE_FLOOR_DB
    quiet = floor_db + QUIET_DB

    onsets: list[float] = []
    last_onset = -1.0
    for i in range(quiet_frames, len(energy_db)):
        if energy_db[i] < threshold:
            continue
        t = i * HOP / sample_rate
        if t - last_onset < REFRACTORY_S:
            continue
        if float(np.max(energy_db[i - quiet_frames:i])) > quiet:
            continue
        frame = np.abs(frames[i])
        first = int(np.argmax(frame >= 0.5 * float(frame.max())))
        t += first / sample_rate
        onsets.append(t)
        last_onset = t
    return onsets


def signal_stats(samples: np.ndarray) -> tuple[float, float]:
    """(peak, signal over quiet floor in dB) for a recording."""
    mono = np.asarray(samples, dtype=np.float32).reshape(-1)
    if mono.size < HOP * 2:
        return 0.0, 0.0
    frames = mono[: (mono.size // HOP) * HOP].reshape(-1, HOP)
    energy_db = 10.0 * np.log10(np.mean(frames * frames, axis=1) + 1e-10)
    floor_db = float(np.percentile(energy_db, 20))
    return float(np.abs(mono).max()), float(energy_db.max() - floor_db)


def match_hits(intended_s: list[float], onsets_s: list[float],
               peak: float = 1.0, snr_db: float = 60.0) -> LatencyReport:
    """Pair each intended hit with the first onset in its window, in order."""
    remaining = sorted(onsets_s)
    samples: list[float] = []
    missed = 0
    for t in sorted(intended_s):
        hit = next((o for o in remaining if t - MATCH_EARLY_S <= o <= t + MATCH_LATE_S), None)
        if hit is None:
            missed += 1
            continue
        remaining.remove(hit)
        samples.append((hit - t) * 1000.0)
    return LatencyReport(
        intended=len(intended_s),
        samples_ms=tuple(samples),
        missed=missed,
        spurious=len(remaining),
        peak=peak,
        snr_db=snr_db,
    )


class MicCapture:
    """A microphone stream whose blocks are stamped on the monotonic clock."""

    def __init__(self, device: str | None = None, sample_rate: int = 48_000,
                 block: int = 512) -> None:
        self._device = device
        self.sample_rate = sample_rate
        self._block = block
        self._stream = None
        self._lock = threading.Lock()
        self._blocks: list[tuple[float, np.ndarray]] = []

    @staticmethod
    def list_inputs() -> list[str]:
        try:
            import sounddevice as sd
        except Exception:
            return []
        return [d["name"] for d in sd.query_devices() if d.get("max_input_channels", 0) > 0]

    @staticmethod
    def resolve_device(available: list[str], requested: str | None) -> str | None:
        if not available:
            return None
        if requested is None:
            return None     # PortAudio's default input
        if requested in available:
            return requested
        lowered = requested.lower()
        for name in available:
            if lowered in name.lower():
                return name
        raise RuntimeError(f"no audio input matched {requested!r}. "
                           f"Available: {', '.join(available)}")

    def start(self) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("latency measurement needs sounddevice: "
                               "uv sync --extra audio") from exc
        device = self.resolve_device(self.list_inputs(), self._device)
        self._stream = sd.InputStream(
            device=device, channels=1, samplerate=self.sample_rate,
            blocksize=self._block, dtype="float32", callback=self._callback)
        self._stream.start()

    def _callback(self, indata, frames, time_info, status) -> None:
        arrival = time.monotonic()
        # PortAudio says how far behind the ADC this block is; failing that,
        # assume it arrived one block after it started.
        try:
            behind = float(time_info.currentTime - time_info.inputBufferAdcTime)
        except Exception:
            behind = frames / self.sample_rate
        if not (0.0 <= behind < 1.0):
            behind = frames / self.sample_rate
        with self._lock:
            self._blocks.append((arrival - behind, indata[:, 0].copy()))

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def audio(self) -> tuple[float, np.ndarray]:
        """Everything recorded so far: (monotonic time of sample 0, samples)."""
        with self._lock:
            blocks = list(self._blocks)
        if not blocks:
            return 0.0, np.zeros(0, dtype=np.float32)
        return blocks[0][0], np.concatenate([b for _, b in blocks])


def run_probe(
    ensemble,
    note: int,
    hits: int,
    gap_s: float,
    capture: MicCapture,
    lead_in_s: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> LatencyReport:
    """Strike `hits` times through the ensemble and listen for each one.

    All hits are scheduled up front: every transport holds early hits and
    lands them itself, so scheduling is not on the measured path. The
    ensemble clock is related to the monotonic clock by sampling both at
    once, several times, and taking the median offset.
    """
    offsets = []
    for _ in range(5):
        offsets.append(ensemble.now_s() - time.monotonic())
    offset = median(offsets)    # ensemble seconds minus monotonic seconds

    start = ensemble.now_s() + lead_in_s
    intended = [start + i * gap_s for i in range(hits)]
    scheduled = [t for t in intended if ensemble.strike_at(note, 100, t, source="latency").ok]

    sleep(max(0.0, intended[-1] + MATCH_LATE_S + 0.5 - ensemble.now_s()))
    first_monotonic, samples = capture.audio()
    onsets = [first_monotonic + offset + t for t in detect_onsets(samples, capture.sample_rate)]
    peak, snr_db = signal_stats(samples)
    return match_hits(scheduled, onsets, peak=peak, snr_db=snr_db)
