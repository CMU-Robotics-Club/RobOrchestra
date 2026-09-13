"""The generated drum voices."""

import numpy as np

from tutti.transports import synth


def test_the_tom_bots_bass_drum_note_sounds_like_a_kick():
    sr = 48_000
    kick = synth.for_role("tom", 36, sr)
    assert np.array_equal(kick, synth.kick(sr))
    assert not np.array_equal(kick, synth.for_role("tom", 45, sr))
    assert np.array_equal(synth.for_role("snare", 36, sr), synth.snare(sr))   # legacy snare fires on 36


def test_a_kick_has_an_attack_small_speakers_can_carry():
    sr = 48_000
    kick = synth.kick(sr)
    assert np.max(np.abs(kick[: sr // 100])) > 0.5      # the first 10 ms
