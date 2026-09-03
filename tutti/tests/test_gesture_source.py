"""Gesture source, driven with synthetic strokes instead of a camera.

The observation feed is structurally typed, so these tests build plain
dataclasses shaped like vision.FrameObservation and never import mediapipe.
The detector, hand tracking and zone logic are all real.
"""

import math
from dataclasses import dataclass

import pytest

from tutti.core import ActuatorModel, Instrument
from tutti.core.ensemble import Ensemble
from tutti.sources.base import Control
from tutti.sources.gesture import ROLE_NOTES, GestureSource, zone_layout
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


def drum_fleet(*roles):
    cycle = {"snare": 105.0, "tom": 105.0, "xylo": 55.0}
    accepts = {"snare": {37, 38, 39, 40}, "tom": {41, 43, 45, 47, 48, 50},
               "xylo": set(range(60, 77))}
    return {
        f"{role}bot": Instrument(
            f"{role}bot", role,
            ActuatorModel(voices=2, cycle_ms=cycle[role], accepts=frozenset(accepts[role])))
        for role in roles
    }


class Harness:
    """A bound gesture source whose ensemble clock follows observation time."""

    def __init__(self, *roles):
        self.wall_ms = [0]
        self.transport = NullTransport()
        self.ensemble = Ensemble(
            drum_fleet(*roles), self.transport,
            clock=lambda: self.wall_ms[0] / 1000.0)
        self.source = GestureSource(display=False)
        self.source.bind(self.ensemble)

    def drum(self, x, handedness="Left", strokes=4, start_ms=0, fps=60,
             top=0.28, bottom=0.66, period_ms=340):
        """Smooth sinusoidal strokes at one screen position, as a player would.

        Starts at the bottom of the swing so the hand lifts before its first
        strike; the detector treats a cold descent as lowering to rest.
        """
        dt = 1000 // fps
        t = start_ms
        mid, amp = (top + bottom) / 2.0, (bottom - top) / 2.0
        while t < start_ms + strokes * period_ms:
            phase = 0.5 + ((t - start_ms) % period_ms) / period_ms
            y = mid - amp * math.cos(2.0 * math.pi * phase)
            self.wall_ms[0] = t
            self.source._process(Observation(t, (hand_at(x, y, handedness),)))
            t += dt
        return t

    def show(self, gesture, at_ms, x=0.5, y=0.3):
        self.wall_ms[0] = at_ms
        self.source._process(Observation(at_ms, (hand_at(x, y, gesture=gesture),)))


# zone layout

def test_zones_split_the_frame_equally_by_role():
    labels, edges, notes = zone_layout(drum_fleet("snare", "tom"))
    assert labels == ("SNARE", "TOM")
    assert edges == (0.5,)
    assert notes == {"SNARE": 38, "TOM": 45}


def test_three_roles_get_three_zones_in_stage_order():
    labels, edges, notes = zone_layout(drum_fleet("snare", "tom", "xylo"))
    assert labels == ("SNARE", "TOM", "XYLO")
    assert edges == pytest.approx((1 / 3, 2 / 3))
    assert notes["XYLO"] == 60


def test_duplicate_roles_share_one_zone():
    fleet = drum_fleet("snare")
    fleet["snarebot2"] = Instrument("snarebot2", "snare", fleet["snarebot"].model)
    labels, edges, _ = zone_layout(fleet)
    assert labels == ("SNARE",)
    assert edges == ()


def test_a_fleet_with_no_known_roles_is_an_error():
    fleet = {"mystery": Instrument("mystery", "theremin",
                                   ActuatorModel(voices=1, cycle_ms=50, accepts=frozenset({70})))}
    with pytest.raises(RuntimeError, match="theremin|role"):
        zone_layout(fleet)


# controls

def test_controls_validate_their_kind():
    with pytest.raises(ValueError):
        Control("bad", "slider")
    with pytest.raises(ValueError):
        Control("bad", "choice")


def test_controls_clamp_to_their_range():
    c = Control("latency_ms", "int", default=90, lo=0, hi=400)
    assert c.clamp(-5) == 0
    assert c.clamp(1000) == 400
    assert c.clamp(90.7) == 90


# strokes end to end: real detector, real ensemble, fake camera

def test_strokes_become_strikes_on_the_transport():
    h = Harness("snare")
    h.drum(x=0.25, strokes=4)
    assert len(h.transport.received) == 4
    assert {hit.note for hit in h.transport.received} == {38}
    assert {hit.bot_id for hit in h.transport.received} == {"snarebot"}


def test_left_and_right_zones_reach_different_bots():
    h = Harness("snare", "tom")
    t = h.drum(x=0.25, handedness="Left", strokes=3)
    h.drum(x=0.80, handedness="Right", strokes=3, start_ms=t + 500)
    notes = [hit.note for hit in h.transport.received]
    assert notes[:3] == [38, 38, 38]
    assert notes[-3:] == [45, 45, 45]


def test_lowering_a_hand_to_rest_is_not_a_strike():
    h = Harness("snare")
    # a hand that only ever descends is being lowered, not played
    t = 0
    for y in [0.2 + 0.02 * i for i in range(25)]:
        h.wall_ms[0] = t
        h.source._process(Observation(t, (hand_at(0.25, y),)))
        t += 16
    assert h.transport.received == []


def test_fist_mutes_and_palm_unmutes():
    h = Harness("snare")
    t = h.drum(x=0.25, strokes=2)
    baseline = len(h.transport.received)
    assert baseline == 2

    h.show("Closed_Fist", at_ms=t + 100)
    t = h.drum(x=0.25, strokes=2, start_ms=t + 600)
    assert len(h.transport.received) == baseline       # muted, nothing lands
    assert h.ensemble.suppressed > 0

    h.show("Open_Palm", at_ms=t + 1200)
    h.drum(x=0.25, strokes=2, start_ms=t + 1700)
    assert len(h.transport.received) > baseline


def test_strikes_respect_the_actuator_limit():
    # Strokes at 70ms intervals against a one-stick bot with a 105ms cycle:
    # physically impossible to play them all, so some must be dropped with a
    # named reason. Sampled at 120fps so the detector can track a stroke that
    # short. 125ms strokes would prove nothing: even one stick sustains those.
    from tutti.core.plan import BotState

    one_stick = Instrument(
        "snarebot", "snare",
        ActuatorModel(voices=1, cycle_ms=105.0, accepts=frozenset({38})))
    h = Harness("snare")
    h.ensemble._states = {"snarebot": BotState(one_stick)}
    h.drum(x=0.25, strokes=8, period_ms=70, fps=120)
    detected = h.ensemble.hits + h.ensemble.dropped
    assert detected >= 4, "detector should track most 70ms strokes at 120fps"
    assert h.ensemble.drop_reasons.get("cycle_not_ready", 0) > 0


def test_velocity_reaches_the_transport_scaled_to_midi():
    h = Harness("snare")
    h.drum(x=0.25, strokes=3)
    for hit in h.transport.received:
        assert 1 <= hit.velocity <= 127
