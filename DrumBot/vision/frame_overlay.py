"""OpenCV overlay utilities for runtime debugging."""

from __future__ import annotations

from collections.abc import Sequence

import cv2
import numpy as np

from vision.gesture_engine import FrameObservation


def draw_overlay(
    frame: np.ndarray,
    observation: FrameObservation | None,
    recent_commands: Sequence[str],
    recent_hits: Sequence[str],
) -> np.ndarray:
    """Draw landmarks, gestures, and most recent emitted protocol lines."""

    output = frame.copy()
    height, width = output.shape[:2]

    if observation is not None:
        for hand in observation.hands:
            for x, y, _ in hand.landmarks:
                pixel_x = int(x * width)
                pixel_y = int(y * height)
                cv2.circle(output, (pixel_x, pixel_y), 2, (0, 200, 255), -1)

            if hand.landmarks:
                anchor_x = int(hand.landmarks[0][0] * width)
                anchor_y = int(hand.landmarks[0][1] * height) - 10
                label = f"{hand.handedness}"
                if hand.top_gesture:
                    label += f" {hand.top_gesture}"
                cv2.putText(
                    output,
                    label,
                    (anchor_x, max(anchor_y, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (80, 255, 80),
                    1,
                    cv2.LINE_AA,
                )

    _draw_history_block(output, title="Commands", lines=recent_commands, origin=(12, 24), color=(0, 255, 0))
    _draw_history_block(output, title="Hits", lines=recent_hits, origin=(12, 132), color=(255, 220, 0))
    return output


def _draw_history_block(
    frame: np.ndarray,
    title: str,
    lines: Sequence[str],
    origin: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    """Draw a titled list of recent debug lines."""

    x0, y0 = origin
    cv2.putText(
        frame,
        title,
        (x0, y0),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2,
        cv2.LINE_AA,
    )
    for index, line in enumerate(reversed(lines)):
        y = y0 + 22 + index * 18
        cv2.putText(
            frame,
            line,
            (x0, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (245, 245, 245),
            1,
            cv2.LINE_AA,
        )
