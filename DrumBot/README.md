# DrumBot Gesture Pipeline

Webcam gesture pipeline for robotic drumming using:

- OpenCV camera capture
- MediaPipe Gesture Recognizer (`LIVE_STREAM`, up to 2 hands)
- Landmark motion-based strike detection
- Drum zone mapping (`HIHAT`, `SNARE`, `TOM`, `CRASH`)
- Dual outputs:
  - newline-delimited serial (`CMD,...`, `HIT,...`)
  - MIDI output (for ESP32 BLE MIDI on macOS)

## Gesture Command Mapping

- `Open_Palm` -> `ARM`
- `Closed_Fist` -> `STOP`
- `Thumb_Up` -> `START_PATTERN`
- `Pointing_Up` -> `NEXT_PATTERN`
- `Victory` -> `FILL_MODE`

Serial examples:

```text
CMD,ARM
HIT,SNARE,0.72,Left,1709939212345
```

## ESP32 BLE MIDI Integration (MacBook)

Your ESP32 firmware receives MIDI notes over BLE and triggers servos on matching notes.  
This app now sends note-on events per zone.

Default zone-to-note map:

- `HIHAT` -> `42`
- `SNARE` -> `38`
- `TOM` -> `45`
- `CRASH` -> `49`

These defaults align with your provided `SnareBot`/`TomBot` note match sets.

### Pairing and Port Selection on macOS

1. Pair/connect the ESP32 BLE MIDI device (e.g. `RobOrchestra_Snare`) in Audio MIDI Setup.
2. List available MIDI outputs:

   ```bash
   python main.py --list-midi-ports
   ```

3. Run with the matched port name (full name or substring):

   ```bash
   python main.py --model models/gesture_recognizer.task --midi-port RobOrchestra
   ```

If `--midi-port` is omitted, the app auto-selects a port containing `RobOrchestra` or `DrumBot`.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Download MediaPipe `gesture_recognizer.task` to:

   ```text
   models/gesture_recognizer.task
   ```

## Run

MIDI + serial enabled:

```bash
python main.py --model models/gesture_recognizer.task --midi-port RobOrchestra --serial-port /dev/ttyUSB0
```

MIDI only:

```bash
python main.py --model models/gesture_recognizer.task --no-serial --midi-port RobOrchestra
```

Serial only:

```bash
python main.py --model models/gesture_recognizer.task --no-midi --serial-port /dev/ttyUSB0
```

No preview window:

```bash
python main.py --model models/gesture_recognizer.task --no-display
```

## Runtime Options

- `--midi-channel` MIDI channel number `1..16` (default: `10`, i.e. channel index `9`)
- `--no-midi` disable MIDI transport
- `--midi-port` select MIDI output by exact name or substring
- `--list-midi-ports` print available outputs and exit

## Config Tuning

Defaults are in `config.py` (`AppConfig`):

- hit detection thresholds (`hit_min_travel`, `hit_velocity_threshold`, `hit_cooldown_ms`)
- zone boundaries (`zone_edges`)
- gesture command cooldown (`gesture_command_cooldown_ms`)
- zone-note mapping (`midi_zone_notes`)
- command-to-CC mapping (`midi_command_cc`)

## Tests

Unit tests cover pure logic modules (no hardware required):

```bash
pytest -q
```

## ESP32 Sketches

Firmware files are included in [`firmware/`](./firmware):

- shared code: `firmware/common/DrumBotCommon.h`
- bots: `firmware/bots/SnareBot/SnareBot.ino`, `firmware/bots/TomBot/TomBot.ino`

Compile/upload instructions are in `firmware/README.md`.

If ESP32-S3 upload fails with `No serial data received`, use the manual recovery
flow in `firmware/README.md` section `ESP32-S3 Upload Recovery (No Serial Data / Port Renames)`.
