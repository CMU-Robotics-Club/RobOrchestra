"""Percussion sounds, generated rather than sampled.

Bundling WAV files would put binaries in a repo that already carries 200 MB of
video it should not. Generating them costs about a millisecond, covers all 17
xylophone pitches without 17 files, and is deterministic enough to test.

These are not meant to sound like the real instruments. They are meant to make
timing audible, which is what the loopback transport is for.
"""

from __future__ import annotations

import numpy as np

A4_HZ = 440.0
A4_MIDI = 69


def note_hz(note: int) -> float:
    return A4_HZ * 2.0 ** ((note - A4_MIDI) / 12.0)


def _normalise(wave: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(wave))
    return (wave / peak if peak > 0 else wave).astype(np.float32)


def snare(sample_rate: int, duration: float = 0.18) -> np.ndarray:
    """Noise burst with a little body under it."""
    t = np.arange(int(sample_rate * duration)) / sample_rate
    rng = np.random.default_rng(seed=1)     # fixed so tests and ears agree
    body = np.sin(2 * np.pi * 185.0 * t) * 0.35
    return _normalise((rng.standard_normal(t.size) * 0.8 + body) * np.exp(-t * 32.0))


def _pitch_drop(t: np.ndarray, base_hz: float, depth: float, rate: float,
                sample_rate: int) -> np.ndarray:
    """A tone whose pitch falls away, which is what makes a drum sound struck."""
    freq = base_hz * (1.0 + depth * np.exp(-t * rate))
    phase = 2.0 * np.pi * np.cumsum(freq) / sample_rate
    return np.sin(phase)


def tom(sample_rate: int, base_hz: float = 110.0, duration: float = 0.40) -> np.ndarray:
    t = np.arange(int(sample_rate * duration)) / sample_rate
    tone = _pitch_drop(t, base_hz, depth=0.55, rate=18.0, sample_rate=sample_rate)
    rng = np.random.default_rng(seed=2)
    attack = rng.standard_normal(t.size) * 0.15 * np.exp(-t * 120.0)
    return _normalise((tone + attack) * np.exp(-t * 7.5))


def kick(sample_rate: int, base_hz: float = 52.0, duration: float = 0.32) -> np.ndarray:
    """A thump with a beater click on the front.

    The fundamental sits where small speakers give up, so the click and a
    faster-decaying octave above carry the attack; without them a kick on a
    laptop is a soft nothing and the groove's first beat goes missing.
    """
    t = np.arange(int(sample_rate * duration)) / sample_rate
    tone = _pitch_drop(t, base_hz, depth=3.2, rate=42.0, sample_rate=sample_rate)
    octave = _pitch_drop(t, base_hz * 2.0, depth=3.2, rate=42.0, sample_rate=sample_rate)
    rng = np.random.default_rng(seed=4)
    click = rng.standard_normal(t.size) * 0.35 * np.exp(-t * 500.0)
    return _normalise((tone + 0.4 * octave * np.exp(-t * 25.0) + click) * np.exp(-t * 11.0))


def mallet(sample_rate: int, note: int, duration: float = 0.65) -> np.ndarray:
    """A struck bar.

    A xylophone bar is undercut so its first overtone sits about a twelfth above
    the fundamental, near the third harmonic, which is why it reads as bright and
    wooden rather than bell-like. The partials decay faster than the fundamental.
    """
    t = np.arange(int(sample_rate * duration)) / sample_rate
    f = note_hz(note)
    wave = (
        np.sin(2 * np.pi * f * t)
        + 0.45 * np.sin(2 * np.pi * f * 3.0 * t) * np.exp(-t * 16.0)
        + 0.18 * np.sin(2 * np.pi * f * 6.0 * t) * np.exp(-t * 30.0)
    )
    rng = np.random.default_rng(seed=3)
    strike = rng.standard_normal(t.size) * 0.10 * np.exp(-t * 300.0)
    return _normalise((wave + strike) * np.exp(-t * 9.0))


def for_role(role: str, note: int, sample_rate: int) -> np.ndarray:
    """Pick a sound for a bot's role, falling back on the note itself."""
    role = role.lower()
    if role == "snare":
        return snare(sample_rate)
    if role == "tom":
        # The tom bot plays the bass drum's notes on its one drum; on the
        # speakers the two are told apart, so a listener can hear which
        # beats are the backbone and which are the decoration.
        if note in (35, 36):
            return kick(sample_rate)
        return tom(sample_rate, base_hz=note_hz(max(note, 36)) * 2.0)
    if role in ("bass", "kick"):
        return kick(sample_rate)
    if role in ("xylo", "marimba", "glock", "bell"):
        return mallet(sample_rate, note)
    # Unknown role: guess from the General MIDI percussion map.
    if note in (35, 36):
        return kick(sample_rate)
    if note in (37, 38, 39, 40):
        return snare(sample_rate)
    if 41 <= note <= 50:
        return tom(sample_rate, base_hz=note_hz(note) * 2.0)
    return mallet(sample_rate, note)
