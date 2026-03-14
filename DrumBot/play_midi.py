"""Play a MIDI file through DrumBot BLE MIDI outputs."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

from transport import MidiClient

try:
    import mido
except Exception:
    mido = None  # type: ignore

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=False, help="Path to .mid file exported from MuseScore")
    parser.add_argument("--midi-port", type=str, default=None, help="MIDI output port name (exact or substring)")
    parser.add_argument("--channel", type=int, default=None, help="Override MIDI channel (1-16). Default: preserve file")
    parser.add_argument("--velocity-scale", type=float, default=1.0, help="Scale note_on velocity (0.0-2.0)")
    parser.add_argument("--loop", action="store_true", help="Loop playback continuously")
    parser.add_argument("--list-midi-ports", action="store_true", help="List available MIDI output ports and exit")
    parser.add_argument("--log-level", type=str, default="INFO", help="Python logging level")
    return parser.parse_args()


def _prepare_message(msg: Any, override_channel: int | None, velocity_scale: float) -> Any:
    out = msg
    if override_channel is not None and hasattr(out, "channel"):
        out = out.copy(channel=override_channel)

    if out.type == "note_on" and getattr(out, "velocity", 0) > 0:
        scaled = int(round(out.velocity * velocity_scale))
        out = out.copy(velocity=min(max(scaled, 1), 127))

    return out


def main() -> int:
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

    if mido is None:
        raise RuntimeError("mido/python-rtmidi is required for MIDI file playback")
    if args.file is None:
        raise ValueError("--file is required unless using --list-midi-ports")
    if not args.file.exists():
        raise FileNotFoundError(f"MIDI file not found: {args.file}")

    override_channel = None
    if args.channel is not None:
        override_channel = min(max(args.channel - 1, 0), 15)

    velocity_scale = min(max(float(args.velocity_scale), 0.0), 2.0)

    midi_client = MidiClient(enabled=True, port_name=args.midi_port, channel=9)
    if not midi_client.is_connected:
        logger.error("No matching MIDI output ports are connected")
        return 1

    logger.info("Active MIDI outputs: %s", ", ".join(midi_client.connected_output_names))
    logger.info("Loading MIDI file: %s", args.file)

    try:
        mid = mido.MidiFile(args.file)
        loop_count = 0
        while True:
            loop_count += 1
            logger.info("Starting playback loop %s", loop_count)
            for msg in mid.play(meta_messages=False):
                out = _prepare_message(msg, override_channel=override_channel, velocity_scale=velocity_scale)
                sent = midi_client.send_message(out)
                if sent == 0:
                    logger.warning("Dropped MIDI message (no active outputs): %s", out)

            if not args.loop:
                break
    except KeyboardInterrupt:
        logger.info("Playback interrupted")
    finally:
        midi_client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
