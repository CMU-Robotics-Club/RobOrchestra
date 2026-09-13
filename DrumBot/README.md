# DrumBot Gesture Pipeline

Webcam gesture pipeline for robotic drumming using:

- OpenCV camera capture
- MediaPipe Gesture Recognizer (`LIVE_STREAM`, up to 2 hands)
- Predictive time-to-contact strike detection (fires ahead of impact to hide
  downstream latency)
- Drop-oldest threaded camera capture
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

### Play a MuseScore-exported MIDI file (no camera required)

Export your score from MuseScore as `.mid`, then play it to the bots:

```bash
python play_midi.py --file /path/to/score.mid --midi-port RobOrchestra
```

## Jam-Along Co-Drummer (Audio Reactive)

Independent demo that listens to live music, tracks tempo/beat in real time,
and plays supportive grooves/fills as a second drummer.

### Quick start

List input devices:

```bash
python jam_along.py --list-audio-devices
```

Run with automatic input selection (prefers loopback devices such as BlackHole
if already installed, otherwise falls back to microphone):

```bash
python jam_along.py --midi-port RobOrchestra
```

Monitor-only dry run (no MIDI output):

```bash
python jam_along.py --dry-run --no-bots
```

Mirror generated MIDI to an additional software output:

```bash
python jam_along.py --midi-port RobOrchestra --mirror-midi-port IAC
```

### Jam-along controls

Type commands while running:

- `+` / `-` — intensity up/down (0-4)
- `fill` — force fill on next eligible bar
- `mute` — toggle mute
- `mode groove|sparse|busy` — groove profile
- `status` — print tracker + scheduler state
- `quit` — stop

### Jam-along CLI flags

| Flag | Description |
|------|-------------|
| `--list-audio-devices` | Print audio inputs and exit |
| `--input-source auto\|mic\|loopback` | Audio source mode (default: `auto`) |
| `--input-device NAME` | Input device substring override |
| `--sample-rate N` | Audio sample rate (default: 48000) |
| `--block-size N` | Audio block size (default: 512) |
| `--min-bpm N` | Minimum expected BPM (default: 70) |
| `--max-bpm N` | Maximum expected BPM (default: 180) |
| `--midi-port NAME` | Bot MIDI output name/substring |
| `--mirror-midi-port NAME` | Optional second MIDI output fanout |
| `--midi-channel N` | MIDI channel 1-16 (default: 10) |
| `--mode groove\|sparse\|busy` | Initial groove mode |
| `--intensity N` | Initial intensity 0-4 (default: 2) |
| `--fill-every-bars N` | Fill cadence in bars (default: 8) |
| `--fill-probability X` | Fill probability 0-1 (default: 0.30) |
| `--no-bots` | Disable bot output |
| `--dry-run` | Run scheduler without MIDI send |
| `--log-level LEVEL` | Logging level (default: INFO) |

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
| `--camera-width N` | Camera frame width (default: 640) |
| `--camera-height N` | Camera frame height (default: 480) |
| `--camera-fps N` | Camera target FPS (default: 60) |
| `--no-mjpg` | Do not request MJPG capture format |
| `--no-mirror` | Disable horizontal mirroring (mirroring is enabled by default) |
| `--display-every N` | Render the preview every Nth processed frame (default: 2) |
| `--stats` | Print pipeline latency and throughput once per second |
| `--detector predictive\|legacy` | Strike detection algorithm (default: `predictive`) |
| `--latency-compensation-ms N` | Fire this far ahead of predicted impact (default: 90) |
| `--strike-landmark-mode palm_centroid\|landmark` | Point whose motion defines a strike |
| `--strike-arm-velocity X` | Downward velocity that arms a stroke (default: 0.45) |
| `--strike-min-travel X` | Minimum stroke travel before firing (default: 0.035) |
| `--strike-refractory-ms N` | Hard floor between hits on one hand (default: 55) |
| `--strike-plane X` | Seed the strike plane (0-1 of frame height) instead of learning it |
| `--no-strike-acceleration` | Use constant-velocity extrapolation only |
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

## Strike Detection

The default detector is **predictive**. Rather than reporting a strike once it
has happened, it fits local kinematics to the hand, models the stroke as one
half-cycle of harmonic motion between the learned top and bottom of the
player's swing, and fires when predicted impact is
`--latency-compensation-ms` away. The note therefore lands on time despite the
camera, MediaPipe, BLE and servo delays stacked behind it.

Three properties matter in practice:

- **The lead is constant.** The old velocity-threshold detector fired whenever
  the hand crossed a fixed speed, so its lead drifted with tempo and stroke
  size (measured: 180 ms of lead at 70 BPM, 63 ms at 180 BPM). The predictive
  detector holds the lead you ask for.
- **Double hits need a lift.** A hand must physically rise before it can strike
  again, so jitter around the trigger point cannot re-fire. This replaces the
  blind cooldown, which either blocked fast playing or let noise through.
- **The strike plane is learned, per hand.** There is no physical drum in front
  of the camera, so each hand tracks where *its own* strokes bottom out and
  adapts as you move. One hand playing high and one playing low keep separate
  planes and do not contaminate each other. `--strike-plane` seeds a starting
  value if you would rather fix it.
- **A strike requires a preparatory lift.** A hand that has only ever travelled
  downwards is being lowered, not played. Without this rule a hand that has
  never drummed borrows the other hand's plane, and simply dropping it to your
  side reads as a strike. The cost is that a hand entering the frame already
  mid-descent will not fire until it lifts once, which is what a player does
  anyway.

Pass `--detector legacy` to A/B against the original algorithm.

### Tuning latency

`--latency-compensation-ms` should equal everything downstream of detection:
MediaPipe inference + BLE MIDI + servo travel.

1. Run with `--stats` and read the reported `capture->dispatch` figure. That is
   the software half, measured live.
2. Add the hardware half. Record your phone's slow-motion video of a hand
   strike and the drum being struck, and count the frames between them.
3. Set the flag to the total. If hits feel late, raise it; if they fire before
   your hand arrives, lower it.

Note that the firmware's per-stick cycle (80 ms hold + 25 ms cooldown) caps
each stick at roughly one hit per 105 ms regardless of anything here.

## Config Tuning

Defaults are in `config.py` (`AppConfig`):

- Camera behavior: `camera_fps`, `camera_mjpg`, `mirror_enabled`
- Predictive detection: `latency_compensation_ms`, `strike_arm_velocity`,
  `strike_min_travel`, `strike_refractory_ms`, `strike_rearm_travel`,
  `strike_fit_window`, `strike_landmark_mode`
- Strike plane learning: `strike_plane_alpha`, `strike_plane_initial`
- Legacy detection: `hit_min_travel`, `hit_velocity_threshold`, `hit_cooldown_ms`
- Duplicate suppression: `hit_zone_cooldown_ms` (short per-zone anti-double-trigger window)
- Tracking recovery: `hand_gap_reset_ms` (drop stale motion after the hand is lost)
- Zone boundaries: `zone_edges`
- Gesture command cooldown: `gesture_command_cooldown_ms`
- Zone-note mapping: `midi_zone_notes`
- Command-to-CC mapping: `midi_command_cc`
- Preview cost: `display_every_n_frames`

## Tests

Unit tests cover pure logic modules (no hardware required):

```bash
pytest -q
```
