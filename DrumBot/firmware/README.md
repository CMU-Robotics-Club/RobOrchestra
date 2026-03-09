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
 
Pick:

- `FQBN` from `arduino-cli board list` for your exact board
- serial `PORT` (example: `/dev/cu.usbserial-0001` on macOS)

## 4) Compile

### Snare bot

```bash
arduino-cli compile --fqbn <FQBN> firmware/bots/SnareBot/SnareBot.ino
```

### Tom bot

```bash
arduino-cli compile --fqbn <FQBN> firmware/bots/TomBot/TomBot.ino
```

## 5) Upload

### Snare bot

```bash
arduino-cli upload -p /dev/cu.usbserial-0001 --fqbn <FQBN> firmware/bots/SnareBot/SnareBot.ino
```

### Tom bot

```bash
arduino-cli upload -p /dev/cu.usbserial-0001 --fqbn <FQBN> firmware/bots/TomBot/TomBot.ino
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

1. Confirm your board is BLE-capable (`ESP32`, `ESP32-S3`, `ESP32-C3`). `ESP32-S2` has no Bluetooth radio.
2. Use the exact board `FQBN` reported by `arduino-cli board list` for both compile and upload.
3. Open serial monitor at `115200` immediately after reset to confirm the sketch is running.
4. Scan with a BLE tool (for example, nRF Connect) and look for `RobOrchestra_Snare` or `RobOrchestra_Tom`.
5. On macOS, connect BLE MIDI via Audio MIDI Setup (not the normal Bluetooth menu).
