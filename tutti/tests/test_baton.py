"""The baton source: the gesture pipeline with every downstroke a beat.

Synthetic strokes stand in for the camera, exactly as in test_gesture_source;
the detector, hand tracking and timing conversion are all real.
"""

import math
from dataclasses import dataclass

from tutti.core import ActuatorModel, Instrument
from tutti.core.ensemble import Ensemble
from tutti.sources.baton import BatonSource
from tutti.transports.loopback import NullTransport


@dataclass(frozen=True)
class Hand:
    hand_id: int
    handedness: str
    landmarks: tuple
    top_gesture: str | None = None


@dataclass(frozen=True)
class Observation:
    timestamp_ms: int
    hands: tuple


def hand_at(x, y, handedness="Left", gesture=None):
    return Hand(hand_id=0, handedness=handedness,
                landmarks=tuple((x, y, 0.0) for _ in range(21)), top_gesture=gesture)


class Harness:
    def __init__(self):
        self.wall_ms = [0]
        self.beats = []
        self.transport = NullTransport()
        fleet = {"snarebot": Instrument("snarebot", "snare", ActuatorModel(
            voices=2, cycle_ms=105.0, accepts=frozenset({38})))}
        self.ensemble = Ensemble(fleet, self.transport, clock=lambda: self.wall_ms[0] / 1000.0)
        self.source = BatonSource(on_beat=lambda t, s: self.beats.append((t, s)), display=False)
        self.source._wall_ms = lambda: float(self.wall_ms[0])
        self.source.bind(self.ensemble)

    def conduct(self, x, strokes=4, start_ms=0, fps=60, top=0.30, bottom=0.62, period_ms=500):
        dt = 1000 // fps
        t = start_ms
        mid, amp = (top + bottom) / 2.0, (bottom - top) / 2.0
        while t < start_ms + strokes * period_ms:
            phase = 0.5 + ((t - start_ms) % period_ms) / period_ms
            y = mid - amp * math.cos(2.0 * math.pi * phase)
            self.wall_ms[0] = t
            self.source._process(Observation(t, (hand_at(x, y),)))
            t += dt
        return t

    def show(self, gesture, at_ms):
        self.wall_ms[0] = at_ms
        self.source._process(Observation(at_ms, (hand_at(0.5, 0.3, gesture=gesture),)))


def test_every_downstroke_anywhere_is_a_beat():
    h = Harness()
    h.conduct(x=0.2, strokes=3)
    h.conduct(x=0.8, strokes=3, start_ms=2000)
    assert len(h.beats) == 6
    assert h.transport.received == []          # beats are reported, not played


def test_beats_are_reported_at_the_predicted_landing_on_the_ensemble_clock():
    h = Harness()
    h.conduct(x=0.5, strokes=4)
    for t, strength in h.beats:
        assert 0.0 <= strength <= 1.0
    # the detector fires ahead of impact, so each beat is a little ahead of
    # the observation that produced it
    gaps = [b - a for a, b in zip([t for t, _ in h.beats], [t for t, _ in h.beats][1:])]
    assert all(abs(g - 0.5) < 0.06 for g in gaps[1:]), gaps


def test_a_fist_still_mutes_the_kit():
    h = Harness()
    h.show("Closed_Fist", at_ms=100)
    assert h.ensemble.muted
    h.show("Open_Palm", at_ms=1200)
    assert not h.ensemble.muted


def test_status_text_is_what_the_window_shows():
    h = Harness()
    assert h.source._overlay_status() == "beats=0"
    h.source.status_text = "120 BPM  bar 3/16"
    assert h.source._overlay_status() == "120 BPM  bar 3/16"
