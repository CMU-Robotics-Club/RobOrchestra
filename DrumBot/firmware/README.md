# ESP32 Firmware

This folder contains Arduino sketches for ESP32 BLE-MIDI drum bots:

- `common/DrumBotCommon.h` shared BLE MIDI + servo logic
- `bots/SnareBot/SnareBot.ino`
- `bots/TomBot/TomBot.ino`

## 1) Prerequisites

- `arduino-cli` installed
- ESP32 board core installed (`esp32:esp32`)
- `Control Surface` library installed

## 2) Install Toolchain + Libraries

Run from the `DrumBot` directory:

```bash
arduino-cli config init
arduino-cli core update-index
arduino-cli core install esp32:esp32
arduino-cli lib install "Control Surface"
```

## 3) Find Board + Port

Connect ESP32 by USB, then:

```bash
arduino-cli board list
```

- `FQBN` from `arduino-cli board list` for exact board
- serial `PORT` (example: `/dev/cu.usbserial-0001` on macOS)

For Adafruit Feather ESP32-S3, use:

```bash
esp32:esp32:adafruit_feather_esp32s3
```

If your Feather variant has no PSRAM, use:

```bash
esp32:esp32:adafruit_feather_esp32s3_nopsram
```

## 4) Compile

### Snare bot

```bash
arduino-cli compile --fqbn esp32:esp32:adafruit_feather_esp32s3 firmware/bots/SnareBot/SnareBot.ino
```

### Tom bot

```bash
arduino-cli compile --fqbn esp32:esp32:adafruit_feather_esp32s3 firmware/bots/TomBot/TomBot.ino
```

## 5) Upload

### Snare bot

```bash
arduino-cli upload -p /dev/cu.usbserial-0001 --fqbn esp32:esp32:adafruit_feather_esp32s3 firmware/bots/SnareBot/SnareBot.ino
```

### Tom bot

```bash
arduino-cli upload -p /dev/cu.usbserial-0001 --fqbn esp32:esp32:adafruit_feather_esp32s3 firmware/bots/TomBot/TomBot.ino
```

## 6) BLE-MIDI Name and Python Port Matching

The sketches advertise as:

- Snare: `RobOrchestra_Snare`
- Tom: `RobOrchestra_Tom`

In this repo, Python can target these names with:

```bash
python main.py --list-midi-ports
python main.py --model models/gesture_recognizer.task --midi-port RobOrchestra --no-serial
```

## 7) Servo and Note Tuning

- Servo timing/pins are in each bot sketch (`*_CONFIG`).
- Note routing is in each `shouldTrigger(...)` switch.
- Channel filtering is controlled by `requireCh10` in config.

## 8) BLE Not Showing Up? Quick Checks

1. Use the exact board `FQBN` reported by `arduino-cli board list` for both compile and upload.
2. Open serial monitor at `115200` immediately after reset to confirm the sketch is running.
3. Scan with a BLE tool (for example, nRF Connect) and look for `RobOrchestra_Snare` or `RobOrchestra_Tom`.
4. On macOS, connect BLE MIDI via Audio MIDI Setup (not the normal Bluetooth menu).
5. This firmware sends periodic MIDI Active Sensing when connected to reduce idle disconnects on hosts that drop silent BLE-MIDI links.

## 8.1) A/B Test BLE Backend (NimBLE vs Bluedroid)

ESP32-S3 defaults to NimBLE. To compare stability against Bluedroid:

### Default backend (NimBLE on ESP32-S3)

```bash
arduino-cli compile --upload -p <PORT> --fqbn esp32:esp32:adafruit_feather_esp32s3 firmware/bots/SnareBot/SnareBot.ino
```

### Forced Bluedroid backend

```bash
arduino-cli compile --upload -p <PORT> --fqbn esp32:esp32:adafruit_feather_esp32s3 \
  --build-property compiler.cpp.extra_flags="-DDRUMBOT_USE_BLUEDROID_BLE=1" \
  firmware/bots/SnareBot/SnareBot.ino
```

On serial monitor, firmware prints the active backend at boot.

## 9) ESP32-S3 Upload Recovery (No Serial Data / Port Renames)

If upload fails with:

- `Failed to connect to ESP32-S3: No serial data received`
- missing port like `/dev/tty.usbmodem1101` after reset

use this deterministic flow.

### Rebuild to fixed output path

```bash
cd DrumBot
arduino-cli compile --fqbn esp32:esp32:adafruit_feather_esp32s3 --build-path /tmp/snare_s3 firmware/bots/SnareBot/SnareBot.ino
```

### Resolve current USB serial port each time

```bash
PORT=$(arduino-cli board list | awk '/ESP32 Family Device/ {print $1; exit}')
echo "$PORT"
```

On macOS this may change between resets (for example `/dev/cu.usbmodem1101` to `/dev/cu.usbmodemF09E9E7835B01`).

### Enter bootloader manually

```bash
esptool --chip esp32s3 --port "$PORT" --before no-reset --after no-reset --connect-attempts 0 chip-id
```

While it prints `Connecting...`:

1. Hold `BOOT`
2. Tap `EN/RESET`
3. Release `BOOT` once `Connected to ESP32-S3` appears

### Flash merged image

```bash
esptool --chip esp32s3 --port "$PORT" --before no-reset --after hard-reset write-flash 0x0 /tmp/snare_s3/SnareBot.ino.merged.bin
```

If flashing fails with a missing port, rerun the `PORT=...` command and retry.
