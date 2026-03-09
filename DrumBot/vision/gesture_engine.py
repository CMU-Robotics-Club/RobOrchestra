"""MediaPipe Gesture Recognizer wrapper for live camera frames."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision


@dataclass(frozen=True)
class HandObservation:
    """One hand's landmarks and top gesture for a frame."""

    hand_id: int
    handedness: str
    landmarks: tuple[tuple[float, float, float], ...]
    top_gesture: str | None
    top_gesture_score: float


@dataclass(frozen=True)
class FrameObservation:
    """Snapshot of recognizer outputs for a timestamp."""

    timestamp_ms: int
    hands: tuple[HandObservation, ...]


class GestureEngine:
    """Runs MediaPipe Gesture Recognizer in LIVE_STREAM mode."""

    def __init__(
        self,
        model_path: Path,
        max_hands: int,
        gesture_score_threshold: float,
    ) -> None:
        if not model_path.exists():
            raise FileNotFoundError(
                f"Gesture model not found at {model_path}. Download gesture_recognizer.task first."
            )

        self._score_threshold = gesture_score_threshold
        self._lock = Lock()
        self._latest: FrameObservation | None = None

        options = vision.GestureRecognizerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.LIVE_STREAM,
            num_hands=max_hands,
            result_callback=self._on_result,
        )
        self._recognizer = vision.GestureRecognizer.create_from_options(options)

    def submit(self, frame_bgr: np.ndarray, timestamp_ms: int) -> None:
        """Submit one frame asynchronously to the recognizer."""

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        self._recognizer.recognize_async(mp_image, timestamp_ms)

    def get_latest(self) -> FrameObservation | None:
        """Get latest completed recognizer output."""

        with self._lock:
            return self._latest

    def close(self) -> None:
        """Release recognizer resources."""

        self._recognizer.close()

    def _on_result(
        self,
        result: vision.GestureRecognizerResult,
        output_image: mp.Image,
        timestamp_ms: int,
    ) -> None:
        """MediaPipe callback invoked when async recognition finishes."""

        del output_image

        hands: list[HandObservation] = []
        for hand_index, landmark_list in enumerate(result.hand_landmarks):
            handedness = self._handedness_at(result, hand_index)
            top_label, top_score = self._gesture_at(result, hand_index)
            if top_score < self._score_threshold:
                top_label = None

            landmarks = tuple((landmark.x, landmark.y, landmark.z) for landmark in landmark_list)
            hands.append(
                HandObservation(
                    hand_id=hand_index,
                    handedness=handedness,
                    landmarks=landmarks,
                    top_gesture=top_label,
                    top_gesture_score=top_score,
                )
            )

        frame_observation = FrameObservation(timestamp_ms=timestamp_ms, hands=tuple(hands))
        with self._lock:
            self._latest = frame_observation

    def _handedness_at(self, result: vision.GestureRecognizerResult, hand_index: int) -> str:
        """Extract handedness label with fallback."""

        if hand_index >= len(result.handedness):
            return "Unknown"
        categories = result.handedness[hand_index]
        if not categories:
            return "Unknown"
        return categories[0].category_name or "Unknown"

    def _gesture_at(
        self, result: vision.GestureRecognizerResult, hand_index: int
    ) -> tuple[str | None, float]:
        """Extract top gesture category with score fallback."""

        if hand_index >= len(result.gestures):
            return None, 0.0
        categories = result.gestures[hand_index]
        if not categories:
            return None, 0.0
        top = categories[0]
        return top.category_name, float(top.score)
