"""Drive the ensemble by drumming in the air at a webcam.

This wraps DrumBot's gesture pipeline (camera, MediaPipe hands, predictive
strike detection) as a tutti Source. The detection code stays in DrumBot/ and
is imported from there: it is actively tuned against real hardware in that
project, and a copy here would drift from it within a month. What this module
owns is the part DrumBot hard-wired: where a detected strike goes. Here it
goes to ensemble.strike(), so the same wave of a hand can hit the speakers,
the old daisy chain, or an ESP32 bot, and a physically impossible strike is
counted and named instead of vanishing.

The screen is split into one vertical zone per role on stage, left to right.
Strike in a zone, and that role's General MIDI note is requested.

Import layering matters here: this module imports nothing heavy, so it can be
loaded and tested anywhere. tracking/config (pure stdlib) load when the source
is constructed; cv2 and mediapipe load only inside start(), because they are
only needed when a real camera is about to open.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from pathlib import Path

from ..core.ensemble import Ensemble
from .base import Control, Source

logger = logging.getLogger(__name__)

# Which General MIDI note a zone requests, by the role standing in that zone.
ROLE_NOTES = {
    "snare": 38,
    "tom": 45,
    "bass": 36,
    "kick": 36,
    "xylo": 60,
}

# Left-to-right zone order. Snare on the left matches the DrumBot demo, so
# muscle memory from one carries to the other.
ROLE_ORDER = ("snare", "tom", "bass", "kick", "xylo")


def find_drumbot_dir() -> Path:
    """Locate the DrumBot directory this source borrows its pipeline from."""
    override = os.environ.get("TUTTI_DRUMBOT_DIR")
    if override:
        return Path(override)
    # src/tutti/sources/gesture.py -> sources -> tutti -> src -> tutti -> repo
    return Path(__file__).resolve().parents[4] / "DrumBot"


def load_drumbot_modules():
    """Import DrumBot's tracking and config modules by path.

    Appended, not prepended, so nothing in DrumBot's directory can shadow an
    installed package by accident.
    """
    drumbot = find_drumbot_dir()
    if not drumbot.is_dir():
        raise RuntimeError(
            f"DrumBot directory not found at {drumbot}. Set TUTTI_DRUMBOT_DIR "
            "if the repo layout is unusual."
        )
    path = str(drumbot)
    if path not in sys.path:
        sys.path.append(path)
    import config as drumbot_config
    import tracking as drumbot_tracking
    return drumbot_config, drumbot_tracking


def zone_layout(instruments: dict) -> tuple[tuple[str, ...], tuple[float, ...], dict[str, int]]:
    """Split the frame into one zone per role on stage.

    Returns (labels, edges, label -> GM note). Only roles with a known note
    get a zone; a xylophone bot next to two drums still leaves the screen
    split three ways, not seventeen.
    """
    roles: list[str] = []
    for inst in instruments.values():
        role = inst.role.lower()
        if role in ROLE_NOTES and role not in roles:
            roles.append(role)
    roles.sort(key=lambda r: ROLE_ORDER.index(r) if r in ROLE_ORDER else len(ROLE_ORDER))

    if not roles:
        raise RuntimeError(
            "no bot on stage has a role this source knows a note for "
            f"(known: {', '.join(sorted(ROLE_NOTES))})"
        )

    labels = tuple(r.upper() for r in roles)
    edges = tuple(i / len(roles) for i in range(1, len(roles)))
    notes = {r.upper(): ROLE_NOTES[r] for r in roles}
    return labels, edges, notes


class GestureSource(Source):
    """Camera in, ensemble.strike() out."""

    name = "gesture"
    controls = (
        Control("latency_ms", "int", default=90, lo=0, hi=400,
                help="fire this far ahead of predicted impact"),
        Control("detector", "choice", default="predictive",
                choices=("predictive", "legacy")),
        Control("mirror", "bool", default=True),
        Control("display", "bool", default=True),
    )

    def __init__(
        self,
        model_path: Path | None = None,
        camera_index: int = 0,
        latency_ms: int = 90,
        detector: str = "predictive",
        mirror: bool = True,
        display: bool = True,
    ) -> None:
        drumbot_config, tracking = load_drumbot_modules()
        self._tracking = tracking
        self._config = drumbot_config.AppConfig(
            detector=detector,
            latency_compensation_ms=latency_ms,
            mirror_enabled=mirror,
            camera_index=camera_index,
        )
        self._model_path = model_path or (find_drumbot_dir() / "models" / "gesture_recognizer.task")
        self._display = display

        self._ensemble: Ensemble | None = None
        self._zone_labels: tuple[str, ...] = ()
        self._zone_notes: dict[str, int] = {}
        self._zone_mapper = None
        self._detector = None
        self._hand_states = None
        self._zone_gate = None
        self._gesture_router = None

        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._running = threading.Event()
        self._error: BaseException | None = None
        self._frame_lock = threading.Lock()
        self._display_frame = None

        # Counters the CLI status line reads. Written by one thread, read by
        # another; ints in CPython make that safe without a lock.
        self.frames = 0
        self.strikes = 0
        self.latency_ms_mean = 0.0

    def bind(self, ensemble: Ensemble) -> None:
        """Wire detection up to an ensemble. Split from start() so tests can
        drive _process() with synthetic observations and no camera."""
        cfg, tracking = self._config, self._tracking
        self._ensemble = ensemble
        self._zone_labels, edges, self._zone_notes = zone_layout(ensemble.instruments)
        self._zone_edges = edges
        self._zone_mapper = tracking.ZoneMapper(zone_edges=edges, zone_labels=self._zone_labels)
        self._zone_gate = tracking.ZoneHitGate(cooldown_ms=cfg.hit_zone_cooldown_ms)
        self._hand_states = tracking.HandStateStore(
            history_size=cfg.hit_history_size, gap_reset_ms=cfg.hand_gap_reset_ms)
        self._gesture_router = tracking.GestureRouter(
            label_to_command=cfg.gesture_to_command,
            cooldown_ms=cfg.gesture_command_cooldown_ms)
        self._detector = self._build_detector()

    def _build_detector(self):
        cfg, tracking = self._config, self._tracking
        if cfg.detector == "legacy":
            return tracking.HitDetector(
                min_travel=cfg.hit_min_travel,
                velocity_threshold=cfg.hit_velocity_threshold,
                cooldown_ms=cfg.hit_cooldown_ms,
                velocity_cap=cfg.hit_velocity_cap,
            )
        return tracking.StrikeDetector(
            latency_compensation_ms=cfg.latency_compensation_ms,
            arm_velocity=cfg.strike_arm_velocity,
            disarm_velocity=cfg.strike_disarm_velocity,
            fallback_velocity=cfg.strike_fallback_velocity,
            min_travel=cfg.strike_min_travel,
            rearm_travel=cfg.strike_rearm_travel,
            refractory_ms=cfg.strike_refractory_ms,
            velocity_cap=cfg.hit_velocity_cap,
            max_lookahead_ms=cfg.strike_max_lookahead_ms,
            fit_window=cfg.strike_fit_window,
            landmark_mode=cfg.strike_landmark_mode,
            landmark_index=cfg.strike_landmark_index,
            use_acceleration=cfg.strike_use_acceleration,
            plane_estimator=self._tracking.StrikePlaneEstimator(
                alpha=cfg.strike_plane_alpha,
                initial=cfg.strike_plane_initial,
                min_observations=cfg.strike_plane_min_observations,
            ),
        )

    def _process(self, observation) -> None:
        """Turn one recognizer snapshot into strikes and commands.

        Structurally typed on purpose: anything with .timestamp_ms and .hands
        (each with .hand_id, .handedness, .landmarks, .top_gesture) works, so
        tests feed synthetic strokes without importing mediapipe.
        """
        assert self._ensemble is not None, "bind() before _process()"
        self._hand_states.prune_stale(current_timestamp_ms=observation.timestamp_ms)

        hands = observation.hands[: self._config.max_hands]
        state_ids = _hand_state_ids(hands)
        for hand, state_id in zip(hands, state_ids):
            hand_state = self._hand_states.get_or_create(
                state_id, hand.handedness, observation.timestamp_ms)

            hit = self._detector.update(
                hand_state=hand_state,
                landmarks=hand.landmarks,
                timestamp_ms=observation.timestamp_ms,
            )
            if hit is not None:
                zone = self._zone_mapper.zone_for_x(hit.x)
                if self._zone_gate.should_emit(zone=zone, timestamp_ms=hit.timestamp_ms):
                    note = self._zone_notes[zone]
                    velocity = max(1, min(127, int(round(hit.velocity * 127))))
                    result = self._ensemble.strike(note, velocity, source=self.name)
                    if result.ok:
                        self.strikes += 1

            command = self._gesture_router.route(
                label=hand.top_gesture,
                handedness=hand.handedness,
                timestamp_ms=observation.timestamp_ms,
            )
            if command is not None:
                self._ensemble.command(command.command)

    def start(self, ensemble: Ensemble) -> None:
        if self._thread is not None:
            return
        self.bind(ensemble)

        # Heavy imports happen here, where a camera is about to open, and
        # nowhere else.
        camera_mod = _import_from_drumbot("camera")
        vision_mod = _import_from_drumbot("vision")
        import cv2

        cfg = self._config
        self._camera = camera_mod.Camera(
            index=cfg.camera_index, width=cfg.camera_width,
            height=cfg.camera_height, fps=cfg.camera_fps, use_mjpg=cfg.camera_mjpg)
        self._engine = vision_mod.GestureEngine(
            model_path=self._model_path, max_hands=cfg.max_hands,
            gesture_score_threshold=cfg.gesture_score_threshold,
            queue_size=cfg.result_queue_size)
        self._cv2 = cv2
        self._vision = vision_mod

        self._camera.start()
        self._stop.clear()
        self._running.clear()
        self._error = None
        self._thread = threading.Thread(target=self._run, name="gesture-source", daemon=True)
        self._thread.start()
        if not self._running.wait(timeout=10.0):
            self.stop()
            raise RuntimeError("gesture pipeline did not start") from self._error

    def _run(self) -> None:
        cfg, cv2 = self._config, self._cv2
        last_ts = -1
        latencies: list[float] = []
        frame = None
        observation = None
        processed_since_render = 0
        try:
            self._running.set()
            while not self._stop.is_set():
                has_frame, frame_read, captured_at = self._camera.read_with_timestamp()
                if has_frame and frame_read is not None:
                    frame = cv2.flip(frame_read, 1) if cfg.mirror_enabled else frame_read
                    self.frames += 1
                    ts = max(int(time.perf_counter() * 1000.0), last_ts + 1)
                    last_ts = ts
                    self._engine.submit(frame_bgr=frame, timestamp_ms=ts, captured_at_s=captured_at)

                pending = self._engine.drain()
                for observation in pending:
                    self._process(observation)
                    processed_since_render += 1
                    if observation.captured_at_s:
                        latencies.append((time.perf_counter() - observation.captured_at_s) * 1000.0)
                        if len(latencies) >= 60:
                            self.latency_ms_mean = sum(latencies) / len(latencies)
                            latencies.clear()

                if (self._display and frame is not None
                        and processed_since_render >= cfg.display_every_n_frames):
                    processed_since_render = 0
                    # Drawing on the frame is plain array work and safe here;
                    # showing it is UI and must happen on the main thread, so
                    # the composed frame is handed over instead. Calling
                    # cv2.imshow from this thread kills the pipeline on macOS
                    # with an opaque C++ exception.
                    shown = self._vision.draw_overlay(
                        frame=frame,
                        observation=observation,
                        recent_commands=(),
                        recent_hits=tuple(
                            f"{r.bot_id} {r.note}" for r in list(self._ensemble.recent)[-4:] if r.ok),
                        zone_edges=self._zone_edges,
                        zone_labels=self._zone_labels,
                        status_line=(f"hits={self.strikes} dropped={self._ensemble.dropped} "
                                     f"latency={self.latency_ms_mean:.0f}ms"),
                    )
                    with self._frame_lock:
                        self._display_frame = shown

                if not has_frame and not pending:
                    time.sleep(0.001)
        except BaseException as exc:
            self._error = exc
            logger.exception("gesture pipeline stopped")
            self._stop.set()
        finally:
            self._running.set()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        if getattr(self, "_engine", None) is not None:
            self._engine.close()
            self._engine = None
        if getattr(self, "_camera", None) is not None:
            self._camera.close()
            self._camera = None
        # Window teardown belongs to whoever showed the window, on the main
        # thread. Nothing UI happens here.

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    @property
    def error(self) -> BaseException | None:
        return self._error

    def poll_display(self):
        """Hand the newest composed frame to the main thread, once.

        Returns None when nothing new has been composed since the last call,
        so the caller never wastes a repaint on a stale frame.
        """
        with self._frame_lock:
            frame = self._display_frame
            self._display_frame = None
            return frame


def _import_from_drumbot(name: str):
    load_drumbot_modules()
    import importlib
    return importlib.import_module(name)


def _hand_state_ids(hands) -> tuple[int, ...]:
    """Stable per-hand state IDs, tolerating duplicate handedness labels.

    Same policy as DrumBot's main loop: a lone Left is 0 and a lone Right is 1
    so a hand keeps its motion history across frames, and duplicates fall back
    to their transient recognizer ID rather than corrupting each other's
    velocity estimates.
    """
    counts: dict[str, int] = {}
    for hand in hands:
        if hand.handedness in ("Left", "Right"):
            counts[hand.handedness] = counts.get(hand.handedness, 0) + 1

    ids = []
    for hand in hands:
        if hand.handedness == "Left" and counts.get("Left", 0) == 1:
            ids.append(0)
        elif hand.handedness == "Right" and counts.get("Right", 0) == 1:
            ids.append(1)
        else:
            ids.append(100 + hand.hand_id)
    return tuple(ids)
