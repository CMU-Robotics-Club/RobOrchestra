"""Actuator models for the bots that exist, measured from their firmware.

These are stand-ins until bots advertise their own capabilities over the wire.
Every number here has a source in the firmware; see .notes/03-instruments.md.

mech_latency_ms is the one value nobody has measured yet. The figures below are
estimates, and until someone puts a piezo on a drum head and records 200 hits,
they are the least trustworthy numbers in the project.
"""

from __future__ import annotations

from .plan import KEYED, POOLED, ActuatorModel, Instrument

# snarebot_servo_midi.ino: stickdown 50 + stickup 40, two servos, fires on note 36.
# LEGACY_SNARE describes the firmware as written; LEGACY_SNARE_GM is the same
# machine addressed in General MIDI, which is what scores are written in. The
# transport maps one to the other.
LEGACY_SNARE = ActuatorModel(
    voices=2,
    cycle_ms=90.0,
    accepts=frozenset({36}),
    voice_mode=POOLED,
    mech_latency_ms=20.0,
)

LEGACY_SNARE_GM = ActuatorModel(
    voices=2,
    cycle_ms=90.0,
    accepts=frozenset({37, 38, 39, 40}),
    voice_mode=POOLED,
    mech_latency_ms=20.0,
)

# tombot_servo_midi.ino: stickdown 70 + stickup 10, two servos, fires on note 37
LEGACY_TOM = ActuatorModel(
    voices=2,
    cycle_ms=80.0,
    accepts=frozenset({37}),
    voice_mode=POOLED,
    mech_latency_ms=20.0,
)

LEGACY_TOM_GM = ActuatorModel(
    voices=2,
    cycle_ms=80.0,
    accepts=frozenset({41, 43, 45, 47, 48, 50, 35, 36}),
    voice_mode=POOLED,
    mech_latency_ms=20.0,
)

# MIDI_xylo_new.ino: 17 solenoids, notes 60-76, KEY_UP_TIME 40ms per key.
# Keyed rather than pooled: a note lands on exactly one solenoid.
# max_concurrent is a guess at the power supply limit and needs measuring.
LEGACY_XYLO = ActuatorModel(
    voices=17,
    cycle_ms=55.0,
    accepts=frozenset(range(60, 77)),
    voice_mode=KEYED,
    lowest_note=60,
    mech_latency_ms=15.0,
    max_concurrent=6,
    sustain=False,
)

# DrumBotCommon.h: kStickDownUs 80ms + kStickUpUs 25ms, kGlobalHitSpacingUs 35ms
_ESP32_CYCLE_MS = 105.0
_ESP32_SPACING_MS = 35.0

ESP32_SNARE = ActuatorModel(
    voices=2,
    cycle_ms=_ESP32_CYCLE_MS,
    accepts=frozenset({37, 38, 39, 40}),
    voice_mode=POOLED,
    spacing_ms=_ESP32_SPACING_MS,
    mech_latency_ms=22.0,
)

# TomBot.ino also routes bass drum (35, 36) to the tom
ESP32_TOM = ActuatorModel(
    voices=2,
    cycle_ms=_ESP32_CYCLE_MS,
    accepts=frozenset({41, 43, 45, 47, 48, 50, 35, 36}),
    voice_mode=POOLED,
    spacing_ms=_ESP32_SPACING_MS,
    mech_latency_ms=22.0,
)

# What each legacy bot's firmware actually listens for, which is not what the
# score says. snarebot_servo_midi.ino fires on note 36; in General MIDI 36 is
# the bass drum and the snare is 38. Translating here means scores can be
# written in GM and old boards still work without being reflashed.
LEGACY_NOTE_MAP = {
    "snarebot-legacy": {gm: 36 for gm in (37, 38, 39, 40)},
    "tombot-legacy": {gm: 37 for gm in (41, 43, 45, 47, 48, 50, 35, 36)},
    # Xylobot already speaks the right numbers, 60-76.
}

# MIDI channel each legacy bot expects, as mido counts them (0-15).
#
# Watch the off-by-one. The Arduino MIDI library reports channels 1-16, so
# Xylobot's `if (channel != 1) return` matches wire channel 0, which is what
# mido calls channel 0. Snarebot and Tombot open MIDI_CHANNEL_OMNI and never
# read the channel at all, so theirs only has to be something.
LEGACY_CHANNELS = {
    "xylobot-01": 0,
    "snarebot-legacy": 0,
    "tombot-legacy": 0,
}

LEGACY_FLEET = {
    "xylobot-01": Instrument("xylobot-01", "xylo", LEGACY_XYLO),
    "snarebot-legacy": Instrument("snarebot-legacy", "snare", LEGACY_SNARE_GM),
    "tombot-legacy": Instrument("tombot-legacy", "tom", LEGACY_TOM_GM),
}

DEFAULT_FLEET = {
    "xylobot-01": Instrument("xylobot-01", "xylo", LEGACY_XYLO),
    "snarebot-01": Instrument("snarebot-01", "snare", ESP32_SNARE),
    "tombot-01": Instrument("tombot-01", "tom", ESP32_TOM),
}


def bind_score(fleet: dict[str, Instrument], score) -> dict[int, list[str]]:
    """Bind each part in a score to the bots that can play it.

    Bots whose role matches come first, then any other bot that accepts every
    note the part actually uses. The fallback is how a bass drum line ends up
    on the tom bot, which is what TomBot.ino already does in firmware with
    ROUTE_BD_TO_TOM. Doing it here makes the routing visible instead of buried
    in a #define.
    """
    notes_by_part: dict[int, set[int]] = {}
    for event in score.events:
        notes_by_part.setdefault(event.part_id, set()).add(event.note)

    binding = {}
    for part in score.parts:
        wanted = notes_by_part.get(part.part_id, set())
        primary = [b.bot_id for b in fleet.values() if b.role == part.role]
        fallback = [
            b.bot_id for b in fleet.values()
            if b.role != part.role and wanted and wanted <= b.model.accepts
        ]
        binding[part.part_id] = primary + fallback
    return binding


def bind_by_role(fleet: dict[str, Instrument], part_roles: dict[int, str]) -> dict[int, list[str]]:
    """Map each part to every bot playing that role."""
    return {pid: [b.bot_id for b in fleet.values() if b.role == role]
            for pid, role in part_roles.items()}
