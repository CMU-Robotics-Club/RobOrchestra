"""Application configuration for DrumBot gesture control."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration values."""

    camera_index: int = 0
    camera_width: int = 1280
    camera_height: int = 720
    camera_fps: int = 30
    max_hands: int = 2
    gesture_model_path: Path = Path("models/gesture_recognizer.task")
    gesture_score_threshold: float = 0.55
    gesture_command_cooldown_ms: int = 900
    hit_history_size: int = 8
    hit_min_travel: float = 0.03
    hit_velocity_threshold: float = 1.0
    hit_cooldown_ms: int = 120
    hit_velocity_cap: float = 2.5
    zone_edges: tuple[float, float, float] = (0.25, 0.5, 0.75)
    zone_labels: tuple[str, str, str, str] = ("HIHAT", "SNARE", "TOM", "CRASH")
    midi_enabled: bool = True
    midi_port_name: str | None = None
    midi_channel: int = 9
    midi_zone_notes: Mapping[str, int] = field(
        default_factory=lambda: {
            "HIHAT": 42,
            "SNARE": 38,
            "TOM": 45,
            "CRASH": 49,
        }
    )
    midi_command_cc: Mapping[str, int] = field(
        default_factory=lambda: {
            "ARM": 20,
            "STOP": 21,
            "START_PATTERN": 22,
            "NEXT_PATTERN": 23,
            "FILL_MODE": 24,
        }
    )
    midi_command_value: int = 127
    serial_port: str | None = None
    serial_baudrate: int = 115200
    serial_enabled: bool = True
    display_window_name: str = "DrumBot Gesture"
    gesture_to_command: Mapping[str, str] = field(
        default_factory=lambda: {
            "Open_Palm": "ARM",
            "Closed_Fist": "STOP",
            "Thumb_Up": "START_PATTERN",
            "Pointing_Up": "NEXT_PATTERN",
            "Victory": "FILL_MODE",
        }
    )
