"""Realtime audio capture utilities for jam-along demo."""

from __future__ import annotations

import queue
import time
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

try:
    import sounddevice as sd
except Exception:
    sd = None  # type: ignore

InputSource = Literal["auto", "mic", "loopback"]

_LOOPBACK_KEYWORDS = (
    "blackhole",
    "loopback",
    "soundflower",
    "vb-cable",
    "virtual",
)


@dataclass(frozen=True)
class AudioDevice:
    """Audio input device descriptor."""

    index: int
    name: str
    max_input_channels: int
    is_loopback: bool


@dataclass(frozen=True)
class AudioFrame:
    """Captured mono audio frame."""

    timestamp_s: float
    samples: np.ndarray


class AudioCapture:
    """Input stream wrapper using callback-based audio capture."""

    def __init__(
        self,
        source: InputSource = "auto",
        device_substring: str | None = None,
        sample_rate: int = 48_000,
        block_size: int = 512,
    ) -> None:
        if sd is None:
            raise RuntimeError("sounddevice is required for live audio capture. Install with: pip install sounddevice")

        self._source = source
        self._device_substring = (device_substring or "").strip() or None
        self._sample_rate = int(sample_rate)
        self._block_size = int(block_size)
        self._frames: queue.Queue[AudioFrame] = queue.Queue(maxsize=64)
        self._stream: Any | None = None

        selected = self.resolve_device(source=source, device_substring=self._device_substring)
        self._device_index = selected.index
        self._device_name = selected.name

    @property
    def selected_device_name(self) -> str:
        return self._device_name

    @staticmethod
    def list_input_devices() -> list[AudioDevice]:
        if sd is None:
            return []

        devices: list[AudioDevice] = []
        for idx, info in enumerate(sd.query_devices()):
            max_in = int(info.get("max_input_channels", 0))
            if max_in <= 0:
                continue
            name = str(info.get("name", f"Device {idx}"))
            lowered = name.lower()
            is_loopback = any(k in lowered for k in _LOOPBACK_KEYWORDS)
            devices.append(AudioDevice(index=idx, name=name, max_input_channels=max_in, is_loopback=is_loopback))
        return devices

    @classmethod
    def resolve_device(cls, source: InputSource, device_substring: str | None) -> AudioDevice:
        devices = cls.list_input_devices()
        if not devices:
            raise RuntimeError("No audio input devices found")

        if device_substring:
            lowered = device_substring.lower()
            matches = [d for d in devices if lowered in d.name.lower()]
            if not matches:
                raise RuntimeError(f"No input device matched substring: {device_substring}")
            return matches[0]

        if source == "loopback":
            loopbacks = [d for d in devices if d.is_loopback]
            if loopbacks:
                return loopbacks[0]
            raise RuntimeError("Requested loopback input, but no loopback device was found")

        if source == "mic":
            non_loop = [d for d in devices if not d.is_loopback]
            preferred = cls._default_input_device(devices)
            if preferred is not None and not preferred.is_loopback:
                return preferred
            if non_loop:
                return non_loop[0]
            return devices[0]

        # auto
        loopbacks = [d for d in devices if d.is_loopback]
        if loopbacks:
            return loopbacks[0]
        preferred = cls._default_input_device(devices)
        if preferred is not None:
            return preferred
        return devices[0]

    @staticmethod
    def _default_input_device(devices: list[AudioDevice]) -> AudioDevice | None:
        if sd is None:
            return None
        default = sd.default.device
        in_index = None
        if isinstance(default, (list, tuple)) and default:
            in_index = int(default[0])
        elif isinstance(default, int):
            in_index = int(default)
        if in_index is None or in_index < 0:
            return None
        for device in devices:
            if device.index == in_index:
                return device
        return None

    def start(self) -> None:
        if sd is None:
            raise RuntimeError("sounddevice is not available")
        if self._stream is not None:
            return

        def _callback(indata: np.ndarray, frames: int, callback_time: Any, status: Any) -> None:
            del frames, callback_time, status
            mono = np.asarray(indata[:, 0], dtype=np.float32).copy()
            frame = AudioFrame(timestamp_s=time.monotonic(), samples=mono)
            try:
                self._frames.put_nowait(frame)
            except queue.Full:
                try:
                    self._frames.get_nowait()
                except queue.Empty:
                    pass
                try:
                    self._frames.put_nowait(frame)
                except queue.Full:
                    pass

        self._stream = sd.InputStream(
            device=self._device_index,
            channels=1,
            samplerate=self._sample_rate,
            blocksize=self._block_size,
            dtype="float32",
            callback=_callback,
        )
        self._stream.start()

    def read(self, timeout_s: float = 0.1) -> AudioFrame | None:
        try:
            return self._frames.get(timeout=timeout_s)
        except queue.Empty:
            return None

    def close(self) -> None:
        if self._stream is None:
            return
        try:
            self._stream.stop()
            self._stream.close()
        finally:
            self._stream = None
