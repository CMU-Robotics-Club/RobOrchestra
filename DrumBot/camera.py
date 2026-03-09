"""Webcam capture wrapper."""

from __future__ import annotations

import cv2
import numpy as np


class Camera:
    """Simple OpenCV camera device abstraction."""

    def __init__(self, index: int, width: int, height: int, fps: int) -> None:
        self._index = index
        self._width = width
        self._height = height
        self._fps = fps
        self._capture: cv2.VideoCapture | None = None

    def start(self) -> None:
        """Open and configure the capture device."""

        capture = cv2.VideoCapture(self._index)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        capture.set(cv2.CAP_PROP_FPS, self._fps)

        if not capture.isOpened():
            capture.release()
            raise RuntimeError(f"Unable to open camera index {self._index}")

        self._capture = capture

    def read(self) -> tuple[bool, np.ndarray]:
        """Read one BGR frame from the camera."""

        if self._capture is None:
            raise RuntimeError("Camera is not started")
        return self._capture.read()

    def close(self) -> None:
        """Release the camera resource."""

        if self._capture is None:
            return
        self._capture.release()
        self._capture = None
