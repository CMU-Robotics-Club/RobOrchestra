"""Co-drummer jam-along demo: listen to music, track beat, and play supporting drums."""

from __future__ import annotations

import argparse
import logging
import queue
import sys
import threading
import time
from dataclasses import dataclass

from jam import AudioCapture, BeatState, BeatTracker, GrooveEngine, MidiRouter, ScheduledNote
from transport import MidiClient

logger = logging.getLogger(__name__)


@dataclass
class RuntimeControls:
    muted: bool = False
    running: bool = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("--list-audio-devices", action="store_true", help="List audio input devices and exit")
    parser.add_argument("--list-midi-ports", action="store_true", help="List MIDI output ports and exit")

    parser.add_argument("--input-source", choices=("auto", "mic", "loopback"), default="auto", help="Audio input source")
    parser.add_argument("--input-device", type=str, default=None, help="Audio input device name substring")
    parser.add_argument("--sample-rate", type=int, default=48_000, help="Audio sample rate")
    parser.add_argument("--block-size", type=int, default=512, help="Audio callback block size")
    parser.add_argument("--min-bpm", type=float, default=70.0, help="Minimum expected BPM")
    parser.add_argument("--max-bpm", type=float, default=180.0, help="Maximum expected BPM")

    parser.add_argument("--midi-port", type=str, default=None, help="Primary MIDI output name (exact or substring)")
    parser.add_argument("--mirror-midi-port", type=str, default=None, help="Optional mirror MIDI output name (exact or substring)")
    parser.add_argument("--midi-channel", type=int, default=10, help="MIDI channel number (1-16)")

    parser.add_argument("--mode", choices=("groove", "sparse", "busy"), default="groove", help="Groove mode")
    parser.add_argument("--intensity", type=int, default=2, help="Intensity level 0-4")
    parser.add_argument("--fill-every-bars", type=int, default=8, help="Fill cadence in bars")
    parser.add_argument("--fill-probability", type=float, default=0.30, help="Probability of fill on fill bars")

    parser.add_argument("--no-bots", action="store_true", help="Disable bot MIDI output")
    parser.add_argument("--dry-run", action="store_true", help="Do not send MIDI, only run scheduler")
    parser.add_argument("--log-level", type=str, default="INFO", help="Python logging level")
    return parser.parse_args()


def _print_audio_devices() -> int:
    devices = AudioCapture.list_input_devices()
    if not devices:
        print("No audio input devices found.")
        return 0

    print("Audio input devices:")
    for device in devices:
        loop_tag = " [loopback]" if device.is_loopback else ""
        print(f"- {device.index}: {device.name} (inputs={device.max_input_channels}){loop_tag}")
    return 0


def _print_midi_ports() -> int:
    ports = MidiClient.list_output_ports()
    if not ports:
        print("No MIDI output ports found.")
        return 0

    print("MIDI output ports:")
    for name in ports:
        print(f"- {name}")
    return 0


def _command_reader(cmd_queue: queue.Queue[str], stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        try:
            line = sys.stdin.readline()
        except Exception:
            break
        if not line:
            time.sleep(0.05)
            continue
        cmd_queue.put(line.strip())


def _print_controls() -> None:
    print("Commands: + | - | fill | mute | mode groove|sparse|busy | status | quit")


def _format_state(state: BeatState, mode: str, intensity: int, muted: bool, input_source: str, device_name: str, pending_count: int) -> str:
    bpm_text = f"{state.bpm:.1f}" if state.bpm is not None else "--"
    lock_text = "Y" if state.locked else "N"
    mute_text = "Y" if muted else "N"
    return (
        f"src={input_source} dev='{device_name}' bpm={bpm_text} conf={state.confidence:.2f} lock={lock_text} "
        f"bar={state.bar_index + 1} beat={state.beat_in_bar} mode={mode} intensity={intensity} mute={mute_text} pending={pending_count}"
    )


def _handle_command(raw: str, controls: RuntimeControls, engine: GrooveEngine, state: BeatState, pending_notes: list[ScheduledNote], input_source: str, device_name: str) -> None:
    command = raw.strip()
    if not command:
        return

    if command == "+":
        engine.set_intensity(engine.intensity + 1)
        print(f"intensity -> {engine.intensity}")
        return
    if command == "-":
        engine.set_intensity(engine.intensity - 1)
        print(f"intensity -> {engine.intensity}")
        return
    if command.lower() == "fill":
        engine.request_fill()
        print("fill scheduled for next eligible bar")
        return
    if command.lower() == "mute":
        controls.muted = not controls.muted
        print(f"mute -> {controls.muted}")
        return
    if command.lower().startswith("mode"):
        parts = command.split()
        if len(parts) != 2:
            print("usage: mode groove|sparse|busy")
            return
        try:
            engine.set_mode(parts[1])
            print(f"mode -> {engine.mode}")
        except ValueError as exc:
            print(str(exc))
        return
    if command.lower() == "status":
        print(_format_state(state, engine.mode, engine.intensity, controls.muted, input_source, device_name, len(pending_notes)))
        return
    if command.lower() in {"quit", "q", "exit"}:
        controls.running = False
        return

    print("Unknown command")
    _print_controls()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.list_audio_devices:
        return _print_audio_devices()
    if args.list_midi_ports:
        return _print_midi_ports()

    capture = AudioCapture(
        source=args.input_source,
        device_substring=args.input_device,
        sample_rate=args.sample_rate,
        block_size=args.block_size,
    )

    midi_channel_zero_based = min(max(args.midi_channel - 1, 0), 15)
    bots_enabled = not args.no_bots and not args.dry_run
    mirror_enabled = bool(args.mirror_midi_port) and not args.dry_run

    bot_client = MidiClient(enabled=bots_enabled, port_name=args.midi_port, channel=midi_channel_zero_based)
    mirror_client = MidiClient(enabled=mirror_enabled, port_name=args.mirror_midi_port, channel=midi_channel_zero_based)
    router = MidiRouter(bot_client=bot_client if bots_enabled else None, mirror_client=mirror_client if mirror_enabled else None, dry_run=args.dry_run)

    tracker = BeatTracker(sample_rate=args.sample_rate, min_bpm=args.min_bpm, max_bpm=args.max_bpm)
    engine = GrooveEngine(
        intensity=args.intensity,
        mode=args.mode,
        fill_every_bars=args.fill_every_bars,
        fill_probability=args.fill_probability,
    )

    controls = RuntimeControls()
    cmd_queue: queue.Queue[str] = queue.Queue()
    stop_event = threading.Event()
    command_thread = threading.Thread(target=_command_reader, args=(cmd_queue, stop_event), daemon=True)

    pending_notes: list[ScheduledNote] = []
    last_state = BeatState(
        bpm=None,
        confidence=0.0,
        locked=False,
        beat_in_bar=1,
        bar_index=0,
        last_onset_s=None,
    )

    capture.start()
    command_thread.start()

    logger.info("Jam-along started")
    logger.info("Audio input: %s", capture.selected_device_name)
    if bots_enabled:
        logger.info("Bot MIDI outputs: %s", ", ".join(bot_client.connected_output_names) or "(none)")
    if mirror_enabled:
        logger.info("Mirror MIDI outputs: %s", ", ".join(mirror_client.connected_output_names) or "(none)")
    if args.dry_run:
        logger.info("Running in dry-run mode (no MIDI will be sent)")
    _print_controls()

    next_status_time = time.monotonic() + 1.0

    try:
        while controls.running:
            while True:
                try:
                    command = cmd_queue.get_nowait()
                except queue.Empty:
                    break
                _handle_command(
                    raw=command,
                    controls=controls,
                    engine=engine,
                    state=last_state,
                    pending_notes=pending_notes,
                    input_source=args.input_source,
                    device_name=capture.selected_device_name,
                )

            frame = capture.read(timeout_s=0.05)
            if frame is not None:
                last_state, beats = tracker.update(frame.samples, frame.timestamp_s)
                for beat_event in beats:
                    pending_notes.extend(engine.notes_for_beat(beat_event, confidence=last_state.confidence))

            now_s = time.monotonic()
            if pending_notes:
                due_notes = [n for n in pending_notes if n.timestamp_s <= now_s + 1e-3]
                pending_notes = [n for n in pending_notes if n.timestamp_s > now_s + 1e-3]
                due_notes.sort(key=lambda n: n.timestamp_s)
                for note in due_notes:
                    if controls.muted:
                        continue
                    sent = router.dispatch(note=note.note, velocity=note.velocity, timestamp_s=note.timestamp_s, source=note.source)
                    if sent == 0 and not args.dry_run and (bots_enabled or mirror_enabled):
                        logger.debug("note dropped: note=%s velocity=%s source=%s", note.note, note.velocity, note.source)

            if now_s >= next_status_time:
                print(_format_state(last_state, engine.mode, engine.intensity, controls.muted, args.input_source, capture.selected_device_name, len(pending_notes)))
                next_status_time = now_s + 1.0

    except KeyboardInterrupt:
        logger.info("Stopping after keyboard interrupt")
    finally:
        stop_event.set()
        capture.close()
        bot_client.close()
        mirror_client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
