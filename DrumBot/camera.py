"""Webcam capture wrapper with drop-oldest threaded reads."""

from __future__ import annotations

import logging
import platform
import time
from dataclasses import dataclass
from threading import Event, Lock, Thread

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CaptureStats:
    """Counters describing how the capture thread is keeping up."""

    frames_captured: int = 0
    frames_delivered: int = 0
    frames_dropped: int = 0
    read_failures: int = 0
    first_frame_at_s: float = 0.0
    last_frame_at_s: float = 0.0

    @property
    def drop_ratio(self) -> float:
        if self.frames_captured == 0:
            return 0.0
        return self.frames_dropped / self.frames_captured

    @property
    def measured_fps(self) -> float:
        """What the camera actually delivers, which is rarely what it claims.

        The requested rate in config is a request. A camera that reports 30 fps
        may deliver 23, and that gap is pure latency: one frame interval sits in
        front of everything else in the pipeline.
        """
        span = self.last_frame_at_s - self.first_frame_at_s
        if span <= 0 or self.frames_captured < 2:
            return 0.0
        return (self.frames_captured - 1) / span


class Camera:
    """OpenCV camera device that always hands back the newest available frame.

    ``cv2.VideoCapture.read()`` returns the *oldest* buffered frame, and
    ``CAP_PROP_BUFFERSIZE`` is not implemented by the macOS AVFoundation
    backend, so a main loop that is even slightly slower than the camera builds
    an unbounded queue of stale frames. A dedicated thread drains the device
    continuously and keeps only the latest frame, which bounds capture latency
    to one frame interval regardless of how long downstream work takes.
    """

    def __init__(self, index: int, width: int, height: int, fps: int, use_mjpg: bool = True) -> None:
        self._index = index
        self._width = width
        self._height = height
        self._fps = fps
        self._use_mjpg = use_mjpg

        self._capture: cv2.VideoCapture | None = None
        self._thread: Thread | None = None
        self._stop = Event()
        self._lock = Lock()
        self._latest: np.ndarray | None = None
        self._latest_timestamp_s: float = 0.0
        self._stats = CaptureStats()

    @property
    def stats(self) -> CaptureStats:
        return self._stats

    def start(self) -> None:
        """Open the device and begin draining it on a background thread."""

        capture = cv2.VideoCapture(self._index, self._preferred_backend())

        # MJPG lets most UVC webcams deliver high frame rates that they cannot
        # sustain with uncompressed output.
        if self._use_mjpg:
            capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        capture.set(cv2.CAP_PROP_FPS, self._fps)
        if hasattr(cv2, "CAP_PROP_BUFFERSIZE"):
            # Honoured on some backends, silently ignored on AVFoundation. The
            # capture thread is what actually bounds latency.
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not capture.isOpened():
            capture.release()
            raise RuntimeError(f"Unable to open camera index {self._index}")

        self._capture = capture
        logger.info(
            "Camera opened: requested %sx%s@%sfps, negotiated %sx%s@%.1ffps",
            self._width, self._height, self._fps,
            int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            capture.get(cv2.CAP_PROP_FPS),
        )

        self._stop.clear()
        self._thread = Thread(target=self._pump, name="camera-capture", daemon=True)
        self._thread.start()

    def _preferred_backend(self) -> int:
        if platform.system() == "Darwin" and hasattr(cv2, "CAP_AVFOUNDATION"):
            return cv2.CAP_AVFOUNDATION
        return cv2.CAP_ANY

    def _pump(self) -> None:
        """Continuously drain the device, keeping only the most recent frame."""

        capture = self._capture
        assert capture is not None
        while not self._stop.is_set():
            ok, frame = capture.read()
            if not ok:
                self._stats.read_failures += 1
                time.sleep(0.002)
                continue

            now = time.perf_counter()
            if self._stats.frames_captured == 0:
                self._stats.first_frame_at_s = now
            self._stats.last_frame_at_s = now
            self._stats.frames_captured += 1
            with self._lock:
                if self._latest is not None:
                    # Previous frame was never consumed; it is now stale.
                    self._stats.frames_dropped += 1
                self._latest = frame
                self._latest_timestamp_s = time.perf_counter()

    def read(self) -> tuple[bool, np.ndarray | None]:
        """Take the newest unread frame, or report that none is pending."""

        with self._lock:
            if self._latest is None:
                return False, None
            frame = self._latest
            self._latest = None
            self._stats.frames_delivered += 1
            return True, frame

    def read_with_timestamp(self) -> tuple[bool, np.ndarray | None, float]:
        """Like :meth:`read`, but also returns when the frame was captured."""

        with self._lock:
            if self._latest is None:
                return False, None, 0.0
            frame = self._latest
            captured_at = self._latest_timestamp_s
            self._latest = None
            self._stats.frames_delivered += 1
            return True, frame, captured_at

    def close(self) -> None:
        """Stop the capture thread and release the device."""

        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        with self._lock:
            self._latest = None
