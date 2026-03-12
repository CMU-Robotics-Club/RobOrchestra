"""Entry point for webcam-driven robotic drum gesture control."""

from __future__ import annotations

import argparse
import logging
import re
import time
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping

import cv2

from camera import Camera
from config import AppConfig
from tracking import CommandEvent, GestureRouter, HandStateStore, HitDetector, HitEvent, ZoneMapper
from transport import CommandMessage, HitMessage, MidiClient, SerialClient
from vision import FrameObservation, GestureEngine, draw_overlay

logger = logging.getLogger(__name__)


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
            logger.debug("sent MIDI note_on note=%s velocity=%.2f outputs=%s", midi_note, hit_event.velocity, sent_to)
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
    parser.add_argument("--no-display", action="store_true", help="Disable OpenCV preview window")
    parser.add_argument("--log-level", type=str, default="INFO", help="Python logging level")

    parser.add_argument("--serial-port", type=str, default=None, help="Serial device path, e.g. /dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=defaults.serial_baudrate, help="Serial baudrate")
    parser.add_argument("--no-serial", action="store_true", help="Disable serial output")

    parser.add_argument("--midi-port", type=str, default=None, help="MIDI output port name (exact or substring)")
    parser.add_argument("--midi-channel", type=int, default=defaults.midi_channel + 1, help="MIDI channel number (1-16)")
    parser.add_argument("--midi-note-off", action="store_true", help="Send note_off immediately after note_on")
    parser.add_argument("--no-midi", action="store_true", help="Disable MIDI output")
    parser.add_argument("--list-midi-ports", action="store_true", help="List available MIDI output ports and exit")
    return parser.parse_args()


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

    config = replace(
        AppConfig(),
        gesture_model_path=args.model,
        camera_index=args.camera_index,
        serial_port=args.serial_port,
        serial_baudrate=args.baudrate,
        serial_enabled=not args.no_serial,
        midi_enabled=not args.no_midi,
        midi_port_name=args.midi_port,
        midi_channel=min(max(args.midi_channel - 1, 0), 15),
        midi_note_off_enabled=args.midi_note_off,
    )

    camera = Camera(
        index=config.camera_index,
        width=config.camera_width,
        height=config.camera_height,
        fps=config.camera_fps,
    )
    gesture_engine = GestureEngine(
        model_path=config.gesture_model_path,
        max_hands=config.max_hands,
        gesture_score_threshold=config.gesture_score_threshold,
    )
    hand_states = HandStateStore(history_size=config.hit_history_size)
    hit_detector = HitDetector(
        min_travel=config.hit_min_travel,
        velocity_threshold=config.hit_velocity_threshold,
        cooldown_ms=config.hit_cooldown_ms,
        velocity_cap=config.hit_velocity_cap,
    )
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

    last_processed_timestamp = -1
    observation: FrameObservation | None = None
    camera.start()
    logger.info("Pipeline started. Press q or ESC in the preview window to quit.")

    try:
        while True:
            has_frame, frame = camera.read()
            if not has_frame:
                continue

            timestamp_ms = int(time.time() * 1000)
            gesture_engine.submit(frame_bgr=frame, timestamp_ms=timestamp_ms)
            latest = gesture_engine.get_latest()
            if latest is not None:
                observation = latest

            if observation is not None and observation.timestamp_ms != last_processed_timestamp:
                last_processed_timestamp = observation.timestamp_ms
                _process_observation(
                    observation=observation,
                    config=config,
                    hand_states=hand_states,
                    hit_detector=hit_detector,
                    zone_mapper=zone_mapper,
                    gesture_router=gesture_router,
                    dispatcher=dispatcher,
                )

            if not args.no_display:
                frame_to_show = draw_overlay(
                    frame=frame,
                    observation=observation,
                    recent_commands=tuple(recent_commands),
                    recent_hits=tuple(recent_hits),
                    zone_edges=zone_edges,
                    zone_labels=zone_labels,
                )
                cv2.imshow(config.display_window_name, frame_to_show)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
    except KeyboardInterrupt:
        logger.info("Stopping after keyboard interrupt")
    finally:
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
    hit_detector: HitDetector,
    zone_mapper: ZoneMapper,
    gesture_router: GestureRouter,
    dispatcher: EventDispatcher,
) -> None:
    """Process one recognizer snapshot."""

    hand_states.prune_stale(current_timestamp_ms=observation.timestamp_ms)

    for hand in observation.hands[: config.max_hands]:
        hand_state_id = _state_id_for_hand(hand.handedness, hand.hand_id)
        hand_state = hand_states.get_or_create(hand_state_id, hand.handedness)

        hit_event = hit_detector.update(
            hand_state=hand_state,
            landmarks=hand.landmarks,
            timestamp_ms=observation.timestamp_ms,
        )
        if hit_event is not None:
            zone = zone_mapper.zone_for_x(hit_event.x)
            dispatcher.emit_hit(zone, hit_event)

        command_event = gesture_router.route(
            label=hand.top_gesture,
            handedness=hand.handedness,
            timestamp_ms=observation.timestamp_ms,
        )
        if command_event is not None:
            dispatcher.emit_command(command_event)


def _state_id_for_hand(handedness: str, fallback_id: int) -> int:
    """Use handedness as stable state key when available."""

    if handedness == "Left":
        return 0
    if handedness == "Right":
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
