"""Entry point for webcam-driven robotic drum gesture control."""

from __future__ import annotations

import argparse
import logging
import time
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping

import cv2

from camera import Camera
from config import AppConfig
from tracking.gesture_router import CommandEvent, GestureRouter
from tracking.hand_state import HandStateStore
from tracking.hit_detector import HitDetector, HitEvent
from tracking.zone_mapper import ZoneMapper
from transport.message_protocol import CommandMessage, HitMessage
from transport.midi_client import MidiClient
from transport.serial_client import SerialClient
from vision.frame_overlay import draw_overlay
from vision.gesture_engine import FrameObservation, GestureEngine

logger = logging.getLogger(__name__)


@dataclass
class EventDispatcher:
    """Fan out runtime events to transports and debug history."""

    serial_client: SerialClient
    midi_client: MidiClient
    midi_zone_notes: Mapping[str, int]
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
            self.midi_client.send_note_on(midi_note, hit_event.velocity)
            logger.debug("sent MIDI note_on note=%s velocity=%.2f", midi_note, hit_event.velocity)
        logger.debug("sent %s", line)

    def emit_command(self, command_event: CommandEvent) -> None:
        """Publish command to serial protocol and optional MIDI CC output."""

        line = CommandMessage(command=command_event.command).to_line()
        self.serial_client.send_line(line)
        self.recent_commands.append(line)

        cc = self.midi_command_cc.get(command_event.command)
        if cc is not None:
            self.midi_client.send_control_change(cc, self.midi_command_value)
            logger.debug("sent MIDI CC cc=%s value=%s", cc, self.midi_command_value)
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
    zone_mapper = ZoneMapper(zone_edges=config.zone_edges, zone_labels=config.zone_labels)
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

    recent_commands: deque[str] = deque(maxlen=5)
    recent_hits: deque[str] = deque(maxlen=5)
    dispatcher = EventDispatcher(
        serial_client=serial_client,
        midi_client=midi_client,
        midi_zone_notes=config.midi_zone_notes,
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


if __name__ == "__main__":
    raise SystemExit(main())
