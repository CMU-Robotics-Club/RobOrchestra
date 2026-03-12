# DrumBot Gesture Pipeline

Webcam gesture pipeline for robotic drumming using:

- OpenCV camera capture
- MediaPipe Gesture Recognizer (`LIVE_STREAM`, up to 2 hands)
- Landmark motion-based strike detection
- Adaptive drum zone mapping by connected bot count (`SNARE`, `TOM`, and inferred extra bots)
- Dual outputs:
  - newline-delimited serial (`CMD,...`, `HIT,...`)
  - MIDI output (for ESP32 BLE MIDI bots on macOS)

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Download MediaPipe `gesture_recognizer.task` to:

   ```text
   models/gesture_recognizer.task
   ```

## ESP32 BLE MIDI Bots

The firmware drives servos in response to BLE MIDI notes. Two bots are provided:

| Bot | BLE Name | Triggers on |
|-----|----------|-------------|
| SnareBot | `RobOrchestra_Snare` | snare (37-40) |
| TomBot | `RobOrchestra_Tom` | toms (41/43/45/47/48/50), bass drum (35/36) |

Each bot filters incoming notes in firmware, so both can receive the same MIDI stream — only matching notes fire the servo.

Compile, upload, and BLE troubleshooting instructions are in [firmware/README.md](firmware/README.md).

### Connecting Both Bots on macOS

1. Open **Audio MIDI Setup** → Window → Show MIDI Studio.
2. Click **Connect** on the first bot, wait for the ESP32 LED to go solid.
3. Wait ~2 seconds, then connect the second bot.
4. Verify both appear:

   ```bash
   python main.py --list-midi-ports
   ```

   You should see two entries like `RobOrchestra_Snare` and `RobOrchestra_Tom`.

## Run

### Both bots simultaneously (recommended)

Use a substring that matches all bot port names:

```bash
python main.py --model models/gesture_recognizer.task --midi-port RobOrchestra --no-serial
```

This opens every MIDI port containing `RobOrchestra` and fans out all notes to both. Each bot ignores notes it doesn't handle.

If `--midi-port` is omitted, the app auto-selects all ports containing `RobOrchestra` or `DrumBot`.

### Single bot only

Target a specific bot by full name:

```bash
python main.py --model models/gesture_recognizer.task --midi-port RobOrchestra_Snare --no-serial
```

### With serial output

```bash
python main.py --model models/gesture_recognizer.task --midi-port RobOrchestra --serial-port /dev/ttyUSB0
```

### No preview window

```bash
python main.py --model models/gesture_recognizer.task --no-display
```

## Gesture Command Mapping

| Gesture | Command |
|---------|---------|
| Open Palm | `ARM` |
| Closed Fist | `STOP` |
| Thumb Up | `START_PATTERN` |
| Pointing Up | `NEXT_PATTERN` |
| Victory | `FILL_MODE` |

Serial protocol examples:

```text
CMD,ARM
HIT,SNARE,0.72,Left,1709939212345
```

## Zone-to-Note Mapping

| Zone | MIDI Note |
|------|-----------|
| `SNARE` | 38 |
| `TOM` | 45 |

The preview is split into equal vertical sections (2/3/4/...) based on the
number of connected bots, and each section is labeled with its bot/zone name.

## Runtime Options

| Flag | Description |
|------|-------------|
| `--model PATH` | Path to `gesture_recognizer.task` |
| `--camera-index N` | OpenCV camera index (default: 0) |
| `--midi-port NAME` | MIDI output port name or substring (opens all matches) |
| `--midi-channel N` | MIDI channel 1-16 (default: 10) |
| `--midi-note-off` | Also send immediate `note_off` after each hit note |
| `--no-midi` | Disable MIDI output |
| `--list-midi-ports` | Print available MIDI outputs and exit |
| `--serial-port PATH` | Serial device path, e.g. `/dev/ttyUSB0` |
| `--baudrate N` | Serial baudrate (default: 115200) |
| `--no-serial` | Disable serial output |
| `--no-display` | Disable OpenCV preview window |
| `--log-level LEVEL` | Python logging level (default: INFO) |

## Servo Calibration

The only value that varies per bot is `upUs` — the servo rest position.
Everything else is a firmware constant:

| Constant | Value | Description |
|----------|-------|-------------|
| `kStrokeOffsetUs` | 450 us | `downUs = upUs - 450` |
| `kStickDownUs` | 80 ms | hold time in strike position |
| `kStickUpUs` | 25 ms | cooldown before next hit |

Run the interactive calibration tool to adjust `upUs` on each connected
bot in real time over BLE MIDI:

```bash
python calibrate.py
```

Controls:

- `+` / `-` — adjust upUs by step size
- Type a number — set upUs directly
- `h` — test hit on selected servo
- `n` — swap between servo 0 / servo 1
- `1`-`9` — switch between connected bots
- `s` — change step size
- `q` — quit and print final `.upUs` values for firmware

## Config Tuning

Defaults are in `config.py` (`AppConfig`):

- Hit detection: `hit_min_travel`, `hit_velocity_threshold`, `hit_cooldown_ms`
- Zone boundaries: `zone_edges`
- Gesture command cooldown: `gesture_command_cooldown_ms`
- Zone-note mapping: `midi_zone_notes`
- Command-to-CC mapping: `midi_command_cc`

## Tests

Unit tests cover pure logic modules (no hardware required):

```bash
pytest -q
```
