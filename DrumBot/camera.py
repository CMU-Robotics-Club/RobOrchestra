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
        ret, frame = self._capture.read()
        if not ret:
            return

        #frame = cv2.flip(frame, 1) #Flip frame horizontally

        #Downsample
        width = int(frame.shape[1] * 0.25)
        height = int(frame.shape[0] * 0.25)
        frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

        return (ret, frame)

    def close(self) -> None:
        """Release the camera resource."""

        if self._capture is None:
            return
        self._capture.release()
        self._capture = None
