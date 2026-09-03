import pytest

from tutti.core import ActuatorModel, Instrument
from tutti.core.ensemble import Ensemble
from tutti.core.fleet import LEGACY_FLEET
from tutti.transports.legacy_din import LegacyDinTransport
from tutti.transports.loopback import LoopbackTransport, NullTransport


class FakeLiveTransport:
    """Controllable clock, recorded sends, configurable live lead."""

    def __init__(self, lead_s=0.0):
        self.t = 0.0
        self.sent = []
        self._lead_s = lead_s

    @property
    def now_s(self):
        return self.t

    def live_lead_s(self, bot_id):
        return self._lead_s

    def send(self, hits):
        self.sent.extend(hits)
        return len(hits)


def snare_model(cycle_ms=100.0):
    return ActuatorModel(voices=2, cycle_ms=cycle_ms, accepts=frozenset({37, 38, 39, 40}))


def band(**bots):
    return {name: Instrument(name, role, model) for name, (role, model) in bots.items()}


def make(lead_s=0.0, **bots):
    transport = FakeLiveTransport(lead_s)
    fleet = bots or {"snare1": ("snare", snare_model())}
    ensemble = Ensemble(band(**fleet), transport)
    return ensemble, transport


# routing

def test_a_strike_reaches_the_transport_immediately():
    ensemble, transport = make()
    result = ensemble.strike(38)
    assert result.ok
    assert len(transport.sent) == 1
    assert transport.sent[0].note == 38
    assert ensemble.hits == 1


def test_play_at_is_now_plus_the_live_lead():
    ensemble, transport = make(lead_s=0.05)
    transport.t = 2.0
    result = ensemble.strike(38)
    assert result.play_at_s == pytest.approx(2.05)


def test_a_note_nobody_accepts_is_named_not_swallowed():
    ensemble, transport = make()
    result = ensemble.strike(99)
    assert not result.ok
    assert result.reason == "note_not_accepted"
    assert transport.sent == []
    assert ensemble.drop_reasons["note_not_accepted"] == 1


def test_rapid_strikes_alternate_voices_then_hit_the_wall():
    ensemble, transport = make()
    first = ensemble.strike(38)
    second = ensemble.strike(38)
    third = ensemble.strike(38)
    assert first.ok and second.ok
    assert {first.voice, second.voice} == {0, 1}
    assert not third.ok
    assert third.reason == "cycle_not_ready"
    assert "cycle" in third.detail


def test_the_wall_clears_once_a_voice_recovers():
    # Both voices fired at t=0, so each is busy for its full 100ms cycle. The
    # 50ms aggregate floor only applies to steady alternation, not bursts.
    ensemble, transport = make()
    ensemble.strike(38)
    ensemble.strike(38)
    transport.t = 0.10
    assert ensemble.strike(38).ok


def test_a_small_overrun_is_nudged_inside_tolerance():
    ensemble, transport = make()
    ensemble.strike(38)
    ensemble.strike(38)
    transport.t = 0.09     # 10ms short of a voice's 100ms cycle
    result = ensemble.strike(38)
    assert result.ok
    assert 0 < result.nudge_ms <= 15.0


def test_a_second_bot_absorbs_the_overflow():
    ensemble, transport = make(
        snare1=("snare", snare_model()),
        snare2=("snare", snare_model()),
    )
    results = [ensemble.strike(38) for _ in range(4)]
    assert all(r.ok for r in results)
    assert {r.bot_id for r in results} == {"snare1", "snare2"}


def test_two_sources_share_one_view_of_a_bot():
    # However many callers there are, the bot has two sticks.
    ensemble, transport = make()
    assert ensemble.strike(38, source="gesture").ok
    assert ensemble.strike(38, source="score").ok
    assert not ensemble.strike(38, source="gesture").ok


# commands

def test_stop_mutes_and_arm_unmutes():
    ensemble, transport = make()
    ensemble.command("STOP")
    result = ensemble.strike(38)
    assert not result.ok and result.reason == "muted"
    assert ensemble.suppressed == 1
    assert transport.sent == []
    ensemble.command("ARM")
    assert ensemble.strike(38).ok


def test_unknown_commands_are_harmless():
    ensemble, transport = make()
    ensemble.command("FILL_MODE")
    assert ensemble.strike(38).ok


def test_status_is_a_readable_summary():
    ensemble, transport = make()
    ensemble.strike(38)
    ensemble.strike(99)
    s = ensemble.status()
    assert s["hits"] == 1
    assert s["dropped"] == 1
    assert s["drop_reasons"] == {"note_not_accepted": 1}
    assert s["bots"] == ["snare1"]


# scheduling ahead: strike_at

def test_strike_at_hands_a_future_hit_over_immediately():
    ensemble, transport = make()
    result = ensemble.strike_at(38, 100, at_s=1.0)
    assert result.ok
    assert result.play_at_s == pytest.approx(1.0)
    assert result.nudge_ms == pytest.approx(0.0)
    assert len(transport.sent) == 1
    assert transport.sent[0].play_at_s == pytest.approx(1.0)
    assert transport.sent[0].requested_s == pytest.approx(1.0)


def test_strike_at_in_the_past_is_dropped_as_too_late():
    ensemble, transport = make(lead_s=0.05)
    transport.t = 2.0
    result = ensemble.strike_at(38, 100, at_s=1.5)
    assert not result.ok
    assert result.reason == "too_late"
    assert "lead" in result.detail
    assert ensemble.drop_reasons["too_late"] == 1
    assert transport.sent == []


def test_strike_at_respects_the_live_lead_floor():
    # now=0 and a 50ms lead: a target 10ms out is unreachable by more than
    # the tolerance, so it must be refused rather than played 40ms late.
    ensemble, transport = make(lead_s=0.05)
    result = ensemble.strike_at(38, 100, at_s=0.01)
    assert not result.ok
    assert result.reason == "too_late"


def test_strike_at_just_inside_the_lead_floor_is_nudged():
    ensemble, transport = make(lead_s=0.05)
    result = ensemble.strike_at(38, 100, at_s=0.04)
    assert result.ok
    assert result.play_at_s == pytest.approx(0.05)
    assert 0 < result.nudge_ms <= 15.0


def test_a_busy_voice_nudges_or_drops_a_scheduled_hit():
    ensemble, transport = make()
    assert ensemble.strike_at(38, 100, at_s=1.0).ok
    assert ensemble.strike_at(38, 100, at_s=1.0).ok
    blocked = ensemble.strike_at(38, 100, at_s=1.05)
    assert not blocked.ok and blocked.reason == "cycle_not_ready"
    nudged = ensemble.strike_at(38, 100, at_s=1.09)
    assert nudged.ok
    assert nudged.play_at_s == pytest.approx(1.10)


def test_future_commitments_block_live_strikes_too():
    ensemble, transport = make()
    ensemble.strike_at(38, 100, at_s=0.0)
    ensemble.strike_at(38, 100, at_s=0.0)
    live = ensemble.strike(38)
    assert not live.ok and live.reason == "cycle_not_ready"


def test_strike_at_respects_mute():
    ensemble, transport = make()
    ensemble.command("STOP")
    result = ensemble.strike_at(38, 100, at_s=1.0)
    assert not result.ok and result.reason == "muted"
    assert ensemble.suppressed == 1
    assert transport.sent == []


def test_max_live_lead_is_the_worst_bot_on_stage():
    ensemble, transport = make(lead_s=0.02)
    assert ensemble.max_live_lead_s() == pytest.approx(0.02)


# live leads on the real transports

def test_legacy_live_lead_is_the_mechanical_latency_not_the_planning_window():
    transport = LegacyDinTransport(LEGACY_FLEET, port=object())
    assert transport.lookahead_s == pytest.approx(0.25)
    assert transport.live_lead_s("snarebot-legacy") == pytest.approx(0.020)
    assert transport.live_lead_s("unknown-bot") == 0.0


def test_loopback_live_lead_is_a_few_audio_blocks():
    transport = LoopbackTransport()
    assert transport.live_lead_s("any") == pytest.approx(transport.lookahead_s)
    assert transport.live_lead_s("any") < 0.05


def test_null_transport_works_with_the_ensemble():
    fleet = band(snare1=("snare", snare_model()))
    ensemble = Ensemble(fleet, NullTransport())
    assert ensemble.strike(38).ok
