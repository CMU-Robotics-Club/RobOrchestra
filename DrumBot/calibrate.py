"""Interactive servo calibration tool for DrumBot BLE MIDI bots.

Connects to all RobOrchestra BLE MIDI devices and lets you adjust the
upUs rest position for each servo in real time.  All other parameters
(stroke offset, stick timing) are baked into firmware constants.

Requires calibration-aware firmware (CC 110-113 in DrumBotCommon.h).
"""

from __future__ import annotations

import sys
import textwrap

try:
    import mido
except ImportError:
    print("mido is not installed. Run: pip install mido python-rtmidi")
    sys.exit(1)

# MIDI CC numbers matching firmware.
CC_SERVO_SELECT = 110
CC_VALUE_COARSE = 111
CC_VALUE_FINE = 112
CC_TEST_HIT = 113

MIDI_CHANNEL = 9  # Channel 10 (0-indexed)

# Firmware constants (mirrored for display only).
STROKE_OFFSET_US = 450
STICK_DOWN_MS = 80
STICK_UP_MS = 25

DEFAULT_UP_US = [1485, 1700]


class Bot:
    """One connected BLE MIDI bot."""

    def __init__(self, port_name: str) -> None:
        self.port_name = port_name
        self.port = mido.open_output(port_name)
        self.up_us = list(DEFAULT_UP_US)

        lower = port_name.lower()
        if "snare" in lower:
            self.label = "Snare"
        elif "tom" in lower:
            self.label = "Tom"
        else:
            self.label = port_name

    def set_up_us(self, servo: int, value: int) -> None:
        """Send a new upUs value to the firmware and move the servo."""
        self.up_us[servo] = value
        coarse = (value >> 7) & 0x7F
        fine = value & 0x7F
        ch = MIDI_CHANNEL
        self.port.send(mido.Message("control_change", channel=ch, control=CC_SERVO_SELECT, value=servo))
        self.port.send(mido.Message("control_change", channel=ch, control=CC_VALUE_COARSE, value=coarse))
        self.port.send(mido.Message("control_change", channel=ch, control=CC_VALUE_FINE, value=fine))

    def test_hit(self, servo: int = 0) -> None:
        """Trigger a test strike."""
        self.port.send(mido.Message("control_change", channel=MIDI_CHANNEL, control=CC_TEST_HIT, value=servo))

    def dump(self) -> None:
        """Ask firmware to print config to serial monitor."""
        self.port.send(mido.Message("control_change", channel=MIDI_CHANNEL, control=CC_SERVO_SELECT, value=127))

    def close(self) -> None:
        self.port.close()


def discover_bots() -> list[Bot]:
    available = list(mido.get_output_names())
    matches = [n for n in available if "roborchestra" in n.lower() or "drumbot" in n.lower()]

    if not matches:
        print("No DrumBot MIDI ports found.")
        if available:
            print("Available ports:")
            for name in available:
                print(f"  - {name}")
        print("\nConnect bots in Audio MIDI Setup first.")
        return []

    bots = []
    for name in matches:
        bots.append(Bot(name))
        print(f"  Connected: {name}")
    return bots


def print_status(bots: list[Bot], bot_idx: int, servo_idx: int, step: int) -> None:
    bot = bots[bot_idx]
    print()
    for i, b in enumerate(bots):
        marker = ">>>" if i == bot_idx else "   "
        print(f"  {marker} [{i + 1}] {b.label} ({b.port_name})")

    print()
    for s in range(2):
        marker = " > " if s == servo_idx else "   "
        up = bot.up_us[s]
        down = up - STROKE_OFFSET_US
        print(f"  {marker}servo {s}:  upUs = {up}   (downUs = {down})")

    print(f"\n  constants:  strokeOffset = {STROKE_OFFSET_US} us"
          f"   stickDown = {STICK_DOWN_MS} ms   stickUp = {STICK_UP_MS} ms")
    print(f"  step: {step}")
    print("  ───────────────────────────────────────────────")
    print("  +/- adjust    <value> set directly    h test hit")
    print("  n   swap servo   1-9 switch bot    s set step    q quit")
    print()


def print_final(bots: list[Bot]) -> None:
    print("\n===== Paste into firmware config =====\n")
    for bot in bots:
        print(f"  {bot.label}:")
        print(f"    .upUs = {{{bot.up_us[0]}, {bot.up_us[1]}}},")
        print()


def main() -> int:
    print(textwrap.dedent("""\

        ╔═══════════════════════════════════╗
        ║    DrumBot Servo Calibrator       ║
        ╚═══════════════════════════════════╝
    """))

    bots = discover_bots()
    if not bots:
        return 1

    bot_idx = 0
    servo_idx = 0
    step = 10

    # Sync defaults to firmware.
    for bot in bots:
        for s in range(2):
            bot.set_up_us(s, bot.up_us[s])

    print_status(bots, bot_idx, servo_idx, step)

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not raw:
            continue

        cmd = raw.lower()
        bot = bots[bot_idx]

        if cmd == "q":
            break
        elif cmd == "n":
            servo_idx = 1 - servo_idx
        elif cmd in ("+", "="):
            bot.set_up_us(servo_idx, bot.up_us[servo_idx] + step)
        elif cmd == "-":
            bot.set_up_us(servo_idx, bot.up_us[servo_idx] - step)
        elif cmd == "h":
            bot.test_hit(servo_idx)
        elif cmd == "d":
            bot.dump()
            print("  (check serial monitor)")
        elif cmd == "s":
            try:
                step = int(input("  step size: ").strip())
            except (ValueError, EOFError, KeyboardInterrupt):
                pass
        elif cmd.isdigit() and 1 <= int(cmd) <= len(bots):
            bot_idx = int(cmd) - 1
        else:
            try:
                value = int(raw)
                bot.set_up_us(servo_idx, value)
            except ValueError:
                print(f"  unknown: {raw}")
                continue

        print_status(bots, bot_idx, servo_idx, step)

    print_final(bots)

    for bot in bots:
        bot.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
