"""MediaPipe gesture recognition and OpenCV overlay."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision


# ── Data types ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class HandObservation:
    hand_id: int
    handedness: str
    landmarks: tuple[tuple[float, float, float], ...]
    top_gesture: str | None
    top_gesture_score: float


@dataclass(frozen=True)
class FrameObservation:
    timestamp_ms: int
    hands: tuple[HandObservation, ...]


# ── Gesture engine ───────────────────────────────────────────────────

class GestureEngine:
    def __init__(self, model_path: Path, max_hands: int, gesture_score_threshold: float) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"Gesture model not found at {model_path}. Download gesture_recognizer.task first.")

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
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        self._recognizer.recognize_async(mp_image, timestamp_ms)

    def get_latest(self) -> FrameObservation | None:
        with self._lock:
            return self._latest

    def close(self) -> None:
        self._recognizer.close()

    def _on_result(self, result: vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int) -> None:
        del output_image
        hands: list[HandObservation] = []
        for i, landmark_list in enumerate(result.hand_landmarks):
            handedness = self._handedness_at(result, i)
            top_label, top_score = self._gesture_at(result, i)
            if top_score < self._score_threshold:
                top_label = None
            landmarks = tuple((lm.x, lm.y, lm.z) for lm in landmark_list)
            hands.append(HandObservation(hand_id=i, handedness=handedness, landmarks=landmarks, top_gesture=top_label, top_gesture_score=top_score))

        with self._lock:
            self._latest = FrameObservation(timestamp_ms=timestamp_ms, hands=tuple(hands))

    def _handedness_at(self, result: vision.GestureRecognizerResult, i: int) -> str:
        if i >= len(result.handedness):
            return "Unknown"
        cats = result.handedness[i]
        return cats[0].category_name or "Unknown" if cats else "Unknown"

    def _gesture_at(self, result: vision.GestureRecognizerResult, i: int) -> tuple[str | None, float]:
        if i >= len(result.gestures):
            return None, 0.0
        cats = result.gestures[i]
        if not cats:
            return None, 0.0
        return cats[0].category_name, float(cats[0].score)


# ── Frame overlay ────────────────────────────────────────────────────

def draw_overlay(
    frame: np.ndarray,
    observation: FrameObservation | None,
    recent_commands: Sequence[str],
    recent_hits: Sequence[str],
    zone_edges: Sequence[float] = (),
    zone_labels: Sequence[str] = (),
) -> np.ndarray:
    output = frame.copy()
    h, w = output.shape[:2]

    _draw_zone_layout(output, zone_edges=zone_edges, zone_labels=zone_labels)

    if observation is not None:
        for hand in observation.hands:
            for x, y, _ in hand.landmarks:
                cv2.circle(output, (int(x * w), int(y * h)), 2, (0, 200, 255), -1)
            if hand.landmarks:
                ax = int(hand.landmarks[0][0] * w)
                ay = int(hand.landmarks[0][1] * h) - 10
                label = hand.handedness
                if hand.top_gesture:
                    label += f" {hand.top_gesture}"
                cv2.putText(output, label, (ax, max(ay, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 255, 80), 1, cv2.LINE_AA)

    _draw_block(output, "Commands", recent_commands, (12, 24), (0, 255, 0))
    _draw_block(output, "Hits", recent_hits, (12, 132), (255, 220, 0))
    return output


def _draw_block(frame: np.ndarray, title: str, lines: Sequence[str], origin: tuple[int, int], color: tuple[int, int, int]) -> None:
    x0, y0 = origin
    cv2.putText(frame, title, (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
    for i, line in enumerate(reversed(lines)):
        cv2.putText(frame, line, (x0, y0 + 22 + i * 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (245, 245, 245), 1, cv2.LINE_AA)


def _draw_zone_layout(frame: np.ndarray, zone_edges: Sequence[float], zone_labels: Sequence[str]) -> None:
    if not zone_labels:
        return

    h, w = frame.shape[:2]
    clamped_edges = [min(max(float(e), 0.0), 1.0) for e in zone_edges]
    boundaries = [0.0, *clamped_edges, 1.0]
    if len(boundaries) != len(zone_labels) + 1:
        return

    for edge in boundaries[1:-1]:
        x = int(edge * w)
        cv2.line(frame, (x, 0), (x, h), (110, 110, 110), 2, cv2.LINE_AA)

    for i, label in enumerate(zone_labels):
        x0 = int(boundaries[i] * w)
        x1 = int(boundaries[i + 1] * w)
        cx = x0 + (x1 - x0) // 2
        text = str(label)
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
        tx = max(8, cx - text_w // 2)
        ty = max(24, text_h + 8)
        cv2.rectangle(frame, (tx - 6, ty - text_h - 8), (tx + text_w + 6, ty + 6), (30, 30, 30), -1)
        cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (240, 240, 240), 2, cv2.LINE_AA)
