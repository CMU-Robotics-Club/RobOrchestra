"""Entry point for webcam-driven robotic drum gesture control."""

from __future__ import annotations

import argparse
import logging
import re
import time
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping, Sequence

import cv2

from camera import Camera
from config import AppConfig
from tracking import (
    CommandEvent,
    GestureRouter,
    HandStateStore,
    HitDetector,
    HitEvent,
    StrikeDetector,
    StrikePlaneEstimator,
    ZoneHitGate,
    ZoneMapper,
)
from transport import CommandMessage, HitMessage, MidiClient, SerialClient
from vision import FrameObservation, GestureEngine, HandObservation, draw_overlay

logger = logging.getLogger(__name__)


class LatencyMonitor:
    """Track capture-to-dispatch latency and pipeline throughput."""

    def __init__(self, window: int = 240) -> None:
        self._samples_ms: deque[float] = deque(maxlen=window)
        self.observations_processed = 0
        self.hits_emitted = 0
        self.hits_suppressed = 0

    def record(self, captured_at_s: float, now_s: float) -> None:
        if captured_at_s <= 0.0:
            return
        self._samples_ms.append((now_s - captured_at_s) * 1000.0)

    def summary(self) -> str:
        if not self._samples_ms:
            return "pipeline latency: (no samples)"
        ordered = sorted(self._samples_ms)
        mean = sum(ordered) / len(ordered)
        p50 = ordered[len(ordered) // 2]
        p95 = ordered[min(int(len(ordered) * 0.95), len(ordered) - 1)]
        return (
            f"capture->dispatch mean={mean:.1f}ms p50={p50:.1f}ms "
            f"p95={p95:.1f}ms max={ordered[-1]:.1f}ms"
        )

    @property
    def mean_ms(self) -> float:
        if not self._samples_ms:
            return 0.0
        return sum(self._samples_ms) / len(self._samples_ms)


@dataclass
class EventDispatcher:
    """Fan out runtime events to transports and debug history."""

    serial_client: SerialClient
    midi_client: MidiClient
    midi_zone_notes: Mapping[str, int]
    midi_note_off_enabled: bool
    midi_command_cc: Mapping[str, int]
    midi_command_value: int
    recent_commands: deque[str]
    recent_hits: deque[str]

    def emit_hit(self, zone: str, hit_event: HitEvent) -> None:
        """Publish hit to serial protocol and MIDI note output."""

        line = HitMessage(
            zone=zone,
            velocity=hit_event.velocity,
            handedness=hit_event.handedness,
            timestamp_ms=hit_event.timestamp_ms,
        ).to_line()
        self.serial_client.send_line(line)
        self.recent_hits.append(line)

        midi_note = self.midi_zone_notes.get(zone)
        if midi_note is not None:
            sent_to = self.midi_client.send_note_on(midi_note, hit_event.velocity)
            if self.midi_note_off_enabled:
                self.midi_client.send_note_off(midi_note)
            if sent_to == 0:
                logger.warning("MIDI note_on dropped (no active outputs). note=%s zone=%s", midi_note, zone)
            logger.debug(
                "sent MIDI note_on note=%s velocity=%.2f lead=%sms outputs=%s",
                midi_note, hit_event.velocity, hit_event.lead_ms, sent_to,
            )
        logger.debug("sent %s", line)

    def emit_command(self, command_event: CommandEvent) -> None:
        """Publish command to serial protocol and optional MIDI CC output."""

        line = CommandMessage(command=command_event.command).to_line()
        self.serial_client.send_line(line)
        self.recent_commands.append(line)

        cc = self.midi_command_cc.get(command_event.command)
        if cc is not None:
            sent_to = self.midi_client.send_control_change(cc, self.midi_command_value)
            if sent_to == 0:
                logger.warning("MIDI CC dropped (no active outputs). cc=%s command=%s", cc, command_event.command)
            logger.debug("sent MIDI CC cc=%s value=%s outputs=%s", cc, self.midi_command_value, sent_to)
        logger.debug("sent %s", line)


def parse_args() -> argparse.Namespace:
    """Parse runtime command-line options."""

    defaults = AppConfig()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=defaults.gesture_model_path, help="Path to gesture_recognizer.task")
    parser.add_argument("--camera-index", type=int, default=defaults.camera_index, help="OpenCV camera index")
    parser.add_argument("--camera-width", type=int, default=defaults.camera_width, help="Camera frame width")
    parser.add_argument("--camera-height", type=int, default=defaults.camera_height, help="Camera frame height")
    parser.add_argument("--camera-fps", type=int, default=defaults.camera_fps, help="Camera target FPS")
    parser.add_argument("--no-mjpg", action="store_true", help="Disable MJPG capture format request")
    parser.add_argument("--no-mirror", action="store_true", help="Disable horizontal mirroring")
    parser.add_argument("--no-display", action="store_true", help="Disable OpenCV preview window")
    parser.add_argument("--display-every", type=int, default=defaults.display_every_n_frames, help="Render preview every Nth processed frame")
    parser.add_argument("--stats", action="store_true", help="Print pipeline latency and throughput once per second")
    parser.add_argument("--log-level", type=str, default="INFO", help="Python logging level")

    parser.add_argument("--detector", choices=("predictive", "legacy"), default=defaults.detector, help="Strike detection algorithm")
    parser.add_argument("--latency-compensation-ms", type=int, default=defaults.latency_compensation_ms, help="Fire this far ahead of predicted impact")
    parser.add_argument("--strike-landmark-mode", choices=("palm_centroid", "landmark"), default=defaults.strike_landmark_mode, help="Point whose motion defines a strike")
    parser.add_argument("--strike-arm-velocity", type=float, default=defaults.strike_arm_velocity, help="Downward velocity that arms a stroke")
    parser.add_argument("--strike-min-travel", type=float, default=defaults.strike_min_travel, help="Minimum stroke travel before firing")
    parser.add_argument("--strike-refractory-ms", type=int, default=defaults.strike_refractory_ms, help="Hard floor between hits on one hand")
    parser.add_argument("--strike-plane", type=float, default=None, help="Seed the strike plane (0-1 of frame height) instead of learning it")
    parser.add_argument("--no-strike-acceleration", action="store_true", help="Use constant-velocity extrapolation only")

    parser.add_argument("--serial-port", type=str, default=None, help="Serial device path, e.g. /dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=defaults.serial_baudrate, help="Serial baudrate")
    parser.add_argument("--no-serial", action="store_true", help="Disable serial output")

    parser.add_argument("--midi-port", type=str, default=None, help="MIDI output port name (exact or substring)")
    parser.add_argument("--midi-channel", type=int, default=defaults.midi_channel + 1, help="MIDI channel number (1-16)")
    parser.add_argument("--midi-note-off", action="store_true", help="Send note_off immediately after note_on")
    parser.add_argument("--no-midi", action="store_true", help="Disable MIDI output")
    parser.add_argument("--list-midi-ports", action="store_true", help="List available MIDI output ports and exit")
    return parser.parse_args()


def _build_config(args: argparse.Namespace) -> AppConfig:
    return replace(
        AppConfig(),
        gesture_model_path=args.model,
        camera_index=args.camera_index,
        camera_width=max(args.camera_width, 160),
        camera_height=max(args.camera_height, 120),
        camera_fps=max(args.camera_fps, 1),
        camera_mjpg=not args.no_mjpg,
        mirror_enabled=not args.no_mirror,
        detector=args.detector,
        latency_compensation_ms=max(args.latency_compensation_ms, 0),
        strike_landmark_mode=args.strike_landmark_mode,
        strike_arm_velocity=args.strike_arm_velocity,
        strike_min_travel=args.strike_min_travel,
        strike_refractory_ms=max(args.strike_refractory_ms, 0),
        strike_plane_initial=args.strike_plane,
        strike_use_acceleration=not args.no_strike_acceleration,
        display_every_n_frames=max(args.display_every, 1),
        serial_port=args.serial_port,
        serial_baudrate=args.baudrate,
        serial_enabled=not args.no_serial,
        midi_enabled=not args.no_midi,
        midi_port_name=args.midi_port,
        midi_channel=min(max(args.midi_channel - 1, 0), 15),
        midi_note_off_enabled=args.midi_note_off,
    )


def _build_detector(config: AppConfig) -> HitDetector | StrikeDetector:
    if config.detector == "legacy":
        logger.info("Strike detection: legacy velocity-threshold crossing")
        return HitDetector(
            min_travel=config.hit_min_travel,
            velocity_threshold=config.hit_velocity_threshold,
            cooldown_ms=config.hit_cooldown_ms,
            velocity_cap=config.hit_velocity_cap,
        )

    logger.info(
        "Strike detection: predictive time-to-contact (latency compensation %sms, landmark=%s)",
        config.latency_compensation_ms, config.strike_landmark_mode,
    )
    return StrikeDetector(
        latency_compensation_ms=config.latency_compensation_ms,
        arm_velocity=config.strike_arm_velocity,
        disarm_velocity=config.strike_disarm_velocity,
        fallback_velocity=config.strike_fallback_velocity,
        min_travel=config.strike_min_travel,
        rearm_travel=config.strike_rearm_travel,
        refractory_ms=config.strike_refractory_ms,
        velocity_cap=config.hit_velocity_cap,
        max_lookahead_ms=config.strike_max_lookahead_ms,
        fit_window=config.strike_fit_window,
        landmark_mode=config.strike_landmark_mode,
        landmark_index=config.strike_landmark_index,
        use_acceleration=config.strike_use_acceleration,
        plane_estimator=StrikePlaneEstimator(
            alpha=config.strike_plane_alpha,
            initial=config.strike_plane_initial,
            min_observations=config.strike_plane_min_observations,
        ),
    )


def main() -> int:
    """Run the live vision-to-transport pipeline."""

    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.list_midi_ports:
        ports = MidiClient.list_output_ports()
        if not ports:
            print("No MIDI output ports found.")
            return 0
        print("MIDI output ports:")
        for name in ports:
            print(f"- {name}")
        return 0

    config = _build_config(args)

    camera = Camera(
        index=config.camera_index,
        width=config.camera_width,
        height=config.camera_height,
        fps=config.camera_fps,
        use_mjpg=config.camera_mjpg,
    )
    gesture_engine = GestureEngine(
        model_path=config.gesture_model_path,
        max_hands=config.max_hands,
        gesture_score_threshold=config.gesture_score_threshold,
        queue_size=config.result_queue_size,
    )
    hand_states = HandStateStore(
        history_size=config.hit_history_size,
        gap_reset_ms=config.hand_gap_reset_ms,
    )
    detector = _build_detector(config)
    zone_hit_gate = ZoneHitGate(cooldown_ms=config.hit_zone_cooldown_ms)
    gesture_router = GestureRouter(
        label_to_command=config.gesture_to_command,
        cooldown_ms=config.gesture_command_cooldown_ms,
    )
    serial_client = SerialClient(
        port=config.serial_port,
        baudrate=config.serial_baudrate,
        enabled=config.serial_enabled,
    )
    midi_client = MidiClient(
        enabled=config.midi_enabled,
        port_name=config.midi_port_name,
        channel=config.midi_channel,
    )
    if midi_client.connected_output_names:
        logger.info("Active MIDI outputs: %s", ", ".join(midi_client.connected_output_names))
    elif config.midi_enabled:
        logger.warning("MIDI is enabled but no output ports are currently connected")

    zone_labels = _resolve_zone_labels(config.zone_labels, midi_client.connected_output_names)
    zone_edges = _resolve_zone_edges(zone_labels, config.zone_edges)
    midi_zone_notes = _resolve_midi_zone_notes(zone_labels, config.midi_zone_notes)
    zone_mapper = ZoneMapper(zone_edges=zone_edges, zone_labels=zone_labels)
    logger.info("Zone layout: %s", ", ".join(f"{zone}→note{midi_zone_notes[zone]}" for zone in zone_labels))

    recent_commands: deque[str] = deque(maxlen=5)
    recent_hits: deque[str] = deque(maxlen=5)
    dispatcher = EventDispatcher(
        serial_client=serial_client,
        midi_client=midi_client,
        midi_zone_notes=midi_zone_notes,
        midi_note_off_enabled=config.midi_note_off_enabled,
        midi_command_cc=config.midi_command_cc,
        midi_command_value=config.midi_command_value,
        recent_commands=recent_commands,
        recent_hits=recent_hits,
    )

    monitor = LatencyMonitor()
    observation: FrameObservation | None = None
    last_submitted_ms = -1
    processed_since_render = 0
    next_stats_s = time.perf_counter() + 1.0

    camera.start()
    logger.info("Pipeline started. Press q or ESC in the preview window to quit (Ctrl-C otherwise).")

    try:
        while True:
            has_frame, frame, captured_at_s = camera.read_with_timestamp()

            if has_frame and frame is not None:
                if config.mirror_enabled:
                    frame = cv2.flip(frame, 1)

                # MediaPipe LIVE_STREAM rejects non-increasing timestamps, and a
                # wall clock can step backwards; perf_counter cannot.
                timestamp_ms = max(int(time.perf_counter() * 1000.0), last_submitted_ms + 1)
                last_submitted_ms = timestamp_ms
                gesture_engine.submit(frame_bgr=frame, timestamp_ms=timestamp_ms, captured_at_s=captured_at_s)

            # Process every observation. Skipping any of them would break the
            # consecutive-sample motion estimate the detector depends on.
            pending = gesture_engine.drain()
            for pending_observation in pending:
                observation = pending_observation
                _process_observation(
                    observation=pending_observation,
                    config=config,
                    hand_states=hand_states,
                    detector=detector,
                    zone_hit_gate=zone_hit_gate,
                    zone_mapper=zone_mapper,
                    gesture_router=gesture_router,
                    dispatcher=dispatcher,
                    monitor=monitor,
                )
                monitor.observations_processed += 1
                monitor.record(pending_observation.captured_at_s, time.perf_counter())
                processed_since_render += 1

            now_s = time.perf_counter()
            if args.stats and now_s >= next_stats_s:
                next_stats_s = now_s + 1.0
                stats = camera.stats
                logger.info(
                    "%s | camera %.1ffps (asked %s) captured=%s delivered=%s "
                    "stale-dropped=%s (%.0f%%) queue-dropped=%s hits=%s suppressed=%s",
                    monitor.summary(), stats.measured_fps, config.camera_fps,
                    stats.frames_captured, stats.frames_delivered,
                    stats.frames_dropped, stats.drop_ratio * 100.0,
                    gesture_engine.dropped_results, monitor.hits_emitted, monitor.hits_suppressed,
                )

            if not args.no_display and frame is not None and processed_since_render >= config.display_every_n_frames:
                processed_since_render = 0
                plane = detector.plane_estimator.global_plane if isinstance(detector, StrikeDetector) else None
                frame_to_show = draw_overlay(
                    frame=frame,
                    observation=observation,
                    recent_commands=tuple(recent_commands),
                    recent_hits=tuple(recent_hits),
                    zone_edges=zone_edges,
                    zone_labels=zone_labels,
                    strike_plane=plane,
                    status_line=f"{monitor.summary()}  hits={monitor.hits_emitted}",
                )
                cv2.imshow(config.display_window_name, frame_to_show)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break

            if not has_frame and not pending:
                # Nothing to do; yield rather than spinning a core.
                time.sleep(0.001)
    except KeyboardInterrupt:
        logger.info("Stopping after keyboard interrupt")
    finally:
        logger.info("Final %s", monitor.summary())
        midi_client.close()
        serial_client.close()
        gesture_engine.close()
        camera.close()
        cv2.destroyAllWindows()

    return 0


def _process_observation(
    observation: FrameObservation,
    config: AppConfig,
    hand_states: HandStateStore,
    detector: HitDetector | StrikeDetector,
    zone_hit_gate: ZoneHitGate,
    zone_mapper: ZoneMapper,
    gesture_router: GestureRouter,
    dispatcher: EventDispatcher,
    monitor: LatencyMonitor,
) -> None:
    """Process one recognizer snapshot."""

    hand_states.prune_stale(current_timestamp_ms=observation.timestamp_ms)

    active_hands = observation.hands[: config.max_hands]
    state_ids = _resolve_hand_state_ids(active_hands)
    for hand, hand_state_id in zip(active_hands, state_ids):
        hand_state = hand_states.get_or_create(hand_state_id, hand.handedness, observation.timestamp_ms)

        hit_event = detector.update(
            hand_state=hand_state,
            landmarks=hand.landmarks,
            timestamp_ms=observation.timestamp_ms,
        )
        if hit_event is not None:
            zone = zone_mapper.zone_for_x(hit_event.x)
            if zone_hit_gate.should_emit(zone=zone, timestamp_ms=hit_event.timestamp_ms):
                dispatcher.emit_hit(zone, hit_event)
                monitor.hits_emitted += 1
            else:
                monitor.hits_suppressed += 1
                logger.debug("suppressed duplicate hit in zone=%s at %s", zone, hit_event.timestamp_ms)

        command_event = gesture_router.route(
            label=hand.top_gesture,
            handedness=hand.handedness,
            timestamp_ms=observation.timestamp_ms,
        )
        if command_event is not None:
            dispatcher.emit_command(command_event)


def _resolve_hand_state_ids(hands: Sequence[HandObservation]) -> tuple[int, ...]:
    """Resolve per-hand state IDs while avoiding handedness collisions."""

    handedness_counts: dict[str, int] = {}
    for hand in hands:
        if hand.handedness in ("Left", "Right"):
            handedness_counts[hand.handedness] = handedness_counts.get(hand.handedness, 0) + 1

    state_ids: list[int] = []
    for hand in hands:
        state_ids.append(_state_id_for_hand(hand.handedness, hand.hand_id, handedness_counts))
    return tuple(state_ids)


def _state_id_for_hand(handedness: str, fallback_id: int, handedness_counts: Mapping[str, int]) -> int:
    """Prefer stable handedness IDs, but avoid collisions when labels duplicate."""

    if handedness == "Left" and handedness_counts.get("Left", 0) == 1:
        return 0
    if handedness == "Right" and handedness_counts.get("Right", 0) == 1:
        return 1
    return 100 + fallback_id


def _resolve_zone_labels(default_zone_labels: tuple[str, ...], output_port_names: tuple[str, ...]) -> tuple[str, ...]:
    """Infer zone labels from connected bot names, falling back to configured defaults."""

    inferred: list[str] = []
    seen_counts: dict[str, int] = {}
    for i, name in enumerate(output_port_names):
        base_zone = _zone_label_for_port(name, i)
        count = seen_counts.get(base_zone, 0) + 1
        seen_counts[base_zone] = count
        inferred.append(base_zone if count == 1 else f"{base_zone}_{count}")

    if inferred:
        return tuple(inferred)
    return default_zone_labels


def _zone_label_for_port(port_name: str, index: int) -> str:
    """Map known bot names to stable labels and sanitize unknown names."""

    lowered = port_name.lower()
    if "snare" in lowered:
        return "SNARE"
    if "tom" in lowered:
        return "TOM"

    normalized = re.sub(r"[^A-Za-z0-9]+", "_", port_name).strip("_").upper()
    if normalized:
        return normalized
    return f"BOT_{index + 1}"


def _resolve_zone_edges(zone_labels: tuple[str, ...], fallback_edges: tuple[float, ...]) -> tuple[float, ...]:
    """Generate evenly split screen zones unless a matching custom fallback is provided."""

    if len(zone_labels) <= 1:
        return ()
    if len(fallback_edges) + 1 == len(zone_labels):
        return fallback_edges
    zone_count = float(len(zone_labels))
    return tuple(i / zone_count for i in range(1, len(zone_labels)))


def _resolve_midi_zone_notes(zone_labels: tuple[str, ...], configured_notes: Mapping[str, int]) -> dict[str, int]:
    """Build a complete zone-to-note mapping for all active zones."""

    notes: dict[str, int] = {}
    for i, zone in enumerate(zone_labels):
        configured = configured_notes.get(zone)
        if configured is None:
            configured = configured_notes.get(re.sub(r"_\d+$", "", zone))
        if configured is not None:
            notes[zone] = int(configured)
            continue
        notes[zone] = _fallback_note_for_zone(zone, i)
    return notes


def _fallback_note_for_zone(zone_label: str, index: int) -> int:
    """Choose practical fallback notes for unknown bot labels."""

    upper = zone_label.upper()
    if "SNARE" in upper:
        return 38
    if "TOM" in upper:
        return 45
    fallback_cycle = (38, 45, 47, 50, 43, 41, 36)
    return fallback_cycle[index % len(fallback_cycle)]


if __name__ == "__main__":
    raise SystemExit(main())
