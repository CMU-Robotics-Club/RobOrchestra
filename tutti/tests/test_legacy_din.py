import threading
import time

import pytest

from tutti.core import ActuatorModel, Instrument, ScheduledHit
from tutti.core.fleet import LEGACY_CHANNELS, LEGACY_FLEET, LEGACY_NOTE_MAP
from tutti.transports.legacy_din import (
    NOTE_ON_S,
    LegacyDinTransport,
    wire_time_s,
)


class FakePort:
    """Stands in for a mido output. Records what would go on the wire."""

    def __init__(self):
        self.messages = []
        self.closed = False
        self._lock = threading.Lock()

    def send(self, msg):
        with self._lock:
            self.messages.append(msg)

    def close(self):
        self.closed = True

    @property
    def notes(self):
        with self._lock:
            return [(m.channel, m.note) for m in self.messages if m.type == "note_on"]


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def hit(t, bot="snarebot-legacy", note=38, vel=100):
    return ScheduledHit(part_id=1, bot_id=bot, voice=0, note=note,
                        velocity=vel, play_at_s=t, requested_s=t)


def make(port=None, clock=None, **kw):
    return LegacyDinTransport(
        LEGACY_FLEET,
        port=port or FakePort(),
        note_map=LEGACY_NOTE_MAP,
        channels=LEGACY_CHANNELS,
        clock=clock,
        **kw,
    )


def wait_for(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.002)
    return False


# wire arithmetic

def test_din_timing_matches_the_spec():
    # 31250 baud, 8N1, three bytes
    assert NOTE_ON_S == pytest.approx(0.00096, abs=1e-5)
    assert wire_time_s(6) == pytest.approx(0.00576, abs=1e-4)
    assert wire_time_s(16) == pytest.approx(0.01536, abs=1e-4)


# port resolution, which replaces picking a device by index

def test_exact_name_wins():
    assert LegacyDinTransport.resolve_port(["A", "B"], "B") == "B"


def test_substring_match_is_case_insensitive():
    assert LegacyDinTransport.resolve_port(["IAC Bus 1", "USB-MIDI-2.0"], "usb") == "USB-MIDI-2.0"


def test_unmatched_request_is_none_rather_than_a_wrong_guess():
    assert LegacyDinTransport.resolve_port(["IAC Bus 1"], "usb") is None


def test_no_request_prefers_a_likely_looking_port():
    assert LegacyDinTransport.resolve_port(["IAC Bus 1", "USB-MIDI-2.0"], None) == "USB-MIDI-2.0"


def test_no_ports_at_all_is_none():
    assert LegacyDinTransport.resolve_port([], "anything") is None


def test_missing_port_raises_with_the_available_names():
    t = LegacyDinTransport(LEGACY_FLEET, port_name="nothing-like-this")
    t.list_ports = staticmethod(lambda: ["IAC Bus 1"])
    with pytest.raises(RuntimeError, match="IAC Bus 1"):
        t.start()


# note translation: scores are General MIDI, firmware is not

def test_gm_snare_becomes_the_note_the_firmware_listens_for():
    t = make()
    assert t.wire_note(hit(0.0, "snarebot-legacy", 38)) == 36
    assert t.wire_note(hit(0.0, "snarebot-legacy", 40)) == 36


def test_gm_toms_all_become_note_37():
    t = make()
    for gm in (41, 43, 45, 47, 48, 50):
        assert t.wire_note(hit(0.0, "tombot-legacy", gm)) == 37


def test_bass_drum_routed_to_the_tom_bot_still_maps():
    t = make()
    assert t.wire_note(hit(0.0, "tombot-legacy", 36)) == 37


def test_xylobot_notes_pass_through_untranslated():
    t = make()
    for note in (60, 67, 76):
        assert t.wire_note(hit(0.0, "xylobot-01", note)) == note


def test_xylobot_is_addressed_on_the_channel_its_firmware_checks():
    # Arduino reports channels 1-16, so its `channel != 1` matches wire channel 0
    assert make().wire_channel(hit(0.0, "xylobot-01", 60)) == 0


# latency compensation, which the old bots cannot do themselves

def test_send_time_is_ahead_of_play_time_by_the_mechanical_latency():
    t = make()
    # LEGACY_SNARE_GM declares 20ms of travel
    assert t._send_at(hit(1.0)) == pytest.approx(0.98)


def test_an_unknown_bot_gets_no_compensation_rather_than_a_crash():
    t = make()
    assert t._send_at(hit(1.0, bot="who")) == pytest.approx(1.0)


# ordering when several land together

def test_low_instruments_are_put_on_the_wire_first():
    t = make()
    order = sorted(
        [hit(0.0, "xylobot-01", 60), hit(0.0, "snarebot-legacy", 38),
         hit(0.0, "tombot-legacy", 45)],
        key=t._order_key,
    )
    assert [h.bot_id for h in order] == ["tombot-legacy", "snarebot-legacy", "xylobot-01"]


# running

def test_hits_reach_the_port_once_their_time_arrives():
    port, clock = FakePort(), FakeClock()
    t = make(port=port, clock=clock)
    t.start()
    try:
        t.send([hit(0.5)])
        assert wait_for(lambda: t.pending == 1)
        assert port.notes == []          # not due yet
        clock.t = 0.6
        assert wait_for(lambda: len(port.notes) == 1)
        assert port.notes == [(0, 36)]   # channel 0, translated to 36
    finally:
        t.close()


def test_nothing_is_sent_before_it_is_due():
    port, clock = FakePort(), FakeClock()
    t = make(port=port, clock=clock)
    t.start()
    try:
        t.send([hit(10.0)])
        time.sleep(0.05)
        assert port.notes == []
    finally:
        t.close()


def test_a_late_hit_is_counted():
    port, clock = FakePort(), FakeClock()
    t = make(port=port, clock=clock)
    t.start()
    try:
        clock.t = 5.0
        t.send([hit(0.0)])           # due four seconds ago
        assert wait_for(lambda: t.sent == 1)
        assert t.late == 1
        assert t.worst_late_ms > 1000
    finally:
        t.close()


def test_velocity_is_flat_unless_asked_for():
    port, clock = FakePort(), FakeClock()
    t = make(port=port, clock=clock)
    t.start()
    try:
        t.send([hit(0.0, vel=42)])
        assert wait_for(lambda: t.sent == 1)
        # legacy bots ignore velocity, so sending the score's value is noise
        assert port.messages[0].velocity == 100
    finally:
        t.close()


def test_velocity_passes_through_when_enabled():
    port, clock = FakePort(), FakeClock()
    t = LegacyDinTransport(LEGACY_FLEET, port=port, note_map=LEGACY_NOTE_MAP,
                           channels=LEGACY_CHANNELS, clock=clock, send_velocity=True)
    t.start()
    try:
        t.send([hit(0.0, vel=42)])
        assert wait_for(lambda: t.sent == 1)
        assert port.messages[0].velocity == 42
    finally:
        t.close()


def test_close_silences_every_channel():
    port = FakePort()
    t = make(port=port)
    t.start()
    t.close()
    offs = [m for m in port.messages if m.type == "control_change" and m.control == 123]
    assert len(offs) == 16


def test_close_is_safe_twice():
    t = make()
    t.start()
    t.close()
    t.close()


def test_an_injected_port_is_not_closed_by_us():
    port = FakePort()
    t = make(port=port)
    t.start()
    t.close()
    assert not port.closed      # we did not open it, so it is not ours to close


def test_start_waits_for_the_sender_to_be_running():
    # Otherwise the first hit goes out as late as the thread took to spin up,
    # which lands on a downbeat.
    t = make()
    t.start()
    try:
        assert t._running.is_set()
    finally:
        t.close()


def test_a_hit_due_immediately_at_start_is_not_late():
    port, clock = FakePort(), FakeClock()
    t = make(port=port, clock=clock)
    t.start()
    try:
        # score time 0.02, minus 20ms compensation, is send_at 0.0, which the
        # 20ms lead-in makes reachable
        t.send([hit(0.02)])
        clock.t = 0.021
        assert wait_for(lambda: t.sent == 1)
        assert t.late == 0
    finally:
        t.close()


def test_lead_in_is_the_largest_head_start_any_bot_needs():
    t = make()
    assert t.lead_in_s == pytest.approx(0.020)     # legacy models declare 20ms


def test_the_downbeat_is_reachable_rather_than_late():
    # Without a lead-in, a hit at score time 0 would have to be sent 20ms before
    # the piece began, and would be reported late every single time.
    port, clock = FakePort(), FakeClock()
    t = make(port=port, clock=clock)
    t.start()
    try:
        t.send([hit(0.0)])
        assert t.now_s == pytest.approx(-0.020)    # time starts before zero
        clock.t = 0.001                            # send_at for this hit is -0.020
        assert wait_for(lambda: t.sent == 1)
        assert t.late == 0
    finally:
        t.close()
