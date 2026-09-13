"""Application configuration for DrumBot gesture control."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration values."""

    # ── Camera ───────────────────────────────────────────────────────
    camera_index: int = 0
    # 640x480 is usually the slowest mode a webcam offers, not the fastest.
    # Many have no native 480p and synthesise it by downscaling, which costs a
    # frame interval. Measured on a MacBook camera: 640x480 delivers 23 fps
    # (43ms) while 1280x720 delivers 30 fps (33ms). Inference cost does not
    # change with resolution, so the larger mode is free. Run probe_latency.py
    # to find the fastest mode on your machine.
    camera_width: int = 1280
    camera_height: int = 720
    camera_fps: int = 60
    camera_mjpg: bool = True
    mirror_enabled: bool = True

    # ── Gesture recognition ──────────────────────────────────────────
    max_hands: int = 2
    gesture_model_path: Path = Path("models/gesture_recognizer.task")
    gesture_score_threshold: float = 0.55
    gesture_command_cooldown_ms: int = 900
    result_queue_size: int = 8

    # ── Strike detection ─────────────────────────────────────────────
    # "predictive" fires ahead of the modelled impact to hide downstream
    # latency; "legacy" is the original velocity-threshold crossing.
    detector: str = "predictive"
    hit_history_size: int = 8

    # Total downstream delay to compensate for: MediaPipe inference + BLE MIDI
    # + servo travel. Measure it, then set it (see README "Tuning latency").
    latency_compensation_ms: int = 90

    # Palm centroid is far steadier than any single landmark, which jitters as
    # fingers articulate during a stroke.
    strike_landmark_mode: str = "palm_centroid"
    strike_landmark_index: int = 9
    strike_fit_window: int = 5
    strike_use_acceleration: bool = True

    # Hysteresis: arm low, disarm lower. A single threshold lets landmark noise
    # cross back and forth and fire repeatedly.
    strike_arm_velocity: float = 0.45
    strike_disarm_velocity: float = 0.10
    strike_fallback_velocity: float = 1.0

    strike_min_travel: float = 0.035
    strike_rearm_travel: float = 0.018
    strike_refractory_ms: int = 55
    strike_max_lookahead_ms: int = 260

    # Adaptive strike plane (where strokes actually bottom out).
    strike_plane_alpha: float = 0.25
    strike_plane_initial: float | None = None
    strike_plane_min_observations: int = 2

    hand_gap_reset_ms: int = 200

    # ── Legacy detector ──────────────────────────────────────────────
    hit_min_travel: float = 0.03
    hit_velocity_threshold: float = 1.0
    hit_cooldown_ms: int = 120
    hit_velocity_cap: float = 2.5
    hit_zone_cooldown_ms: int = 35

    # ── Zones ────────────────────────────────────────────────────────
    zone_edges: tuple[float, ...] = (0.5,)
    zone_labels: tuple[str, ...] = ("SNARE", "TOM")

    # ── MIDI ─────────────────────────────────────────────────────────
    midi_enabled: bool = True
    midi_port_name: str | None = None
    midi_channel: int = 9
    midi_note_off_enabled: bool = False
    midi_zone_notes: Mapping[str, int] = field(
        default_factory=lambda: {
            "SNARE": 38,
            "TOM": 45,
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

    # ── Serial ───────────────────────────────────────────────────────
    serial_port: str | None = None
    serial_baudrate: int = 115200
    serial_enabled: bool = True

    # ── Display ──────────────────────────────────────────────────────
    # Rendering and imshow sit on the critical path, so only paint every Nth
    # processed frame.
    display_window_name: str = "DrumBot Gesture"
    display_every_n_frames: int = 2

    gesture_to_command: Mapping[str, str] = field(
        default_factory=lambda: {
            "Open_Palm": "ARM",
            "Closed_Fist": "STOP",
            "Thumb_Up": "START_PATTERN",
            "Pointing_Up": "NEXT_PATTERN",
            "Victory": "FILL_MODE",
        }
    )
