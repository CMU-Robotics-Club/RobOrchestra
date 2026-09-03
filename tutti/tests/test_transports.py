import numpy as np
import pytest

from tutti.core import ActuatorModel, Instrument, Plan, ScheduledHit
from tutti.core.player import play_plan
from tutti.transports import synth
from tutti.transports.loopback import Mixer, NullTransport


def hit(t, note=38, bot="snarebot-01", vel=100, voice=0):
    return ScheduledHit(part_id=1, bot_id=bot, voice=voice, note=note,
                        velocity=vel, play_at_s=t, requested_s=t)


# synth

@pytest.mark.parametrize("fn", [synth.snare, synth.kick, synth.tom])
def test_percussion_is_normalised_and_finite(fn):
    w = fn(48_000)
    assert w.dtype == np.float32
    assert np.isfinite(w).all()
    assert np.max(np.abs(w)) == pytest.approx(1.0)


def test_note_hz_is_equal_temperament():
    assert synth.note_hz(69) == pytest.approx(440.0)
    assert synth.note_hz(60) == pytest.approx(261.63, abs=0.01)
    assert synth.note_hz(81) == pytest.approx(880.0)


def test_mallet_pitch_tracks_the_note():
    def peak_hz(note):
        w = synth.mallet(48_000, note)
        spec = np.abs(np.fft.rfft(w))
        return np.fft.rfftfreq(w.size, 1 / 48_000)[np.argmax(spec)]

    assert peak_hz(60) == pytest.approx(synth.note_hz(60), rel=0.05)
    assert peak_hz(72) == pytest.approx(synth.note_hz(72), rel=0.05)


def test_generation_is_deterministic():
    assert np.array_equal(synth.snare(48_000), synth.snare(48_000))


def test_role_picks_a_sound_and_falls_back_on_the_note():
    sr = 48_000
    assert np.array_equal(synth.for_role("snare", 38, sr), synth.snare(sr))
    # unknown role, GM bass drum note
    assert np.array_equal(synth.for_role("mystery", 36, sr), synth.kick(sr))


# mixer

def test_silence_when_nothing_is_scheduled():
    m = Mixer(sample_rate=1000)
    assert not m.render(100).any()
    assert m.frame == 100


def test_a_hit_lands_on_its_exact_sample():
    m = Mixer(sample_rate=1000, master_gain=1.0)
    m.schedule(hit(0.5))                 # sample 500
    block = m.render(1000)
    assert not block[:500].any()
    assert block[500:].any()


def test_placement_is_sample_accurate_not_block_quantised():
    # 0.1234s at 1kHz is sample 123, mid block
    m = Mixer(sample_rate=1000, master_gain=1.0)
    m.schedule(hit(0.1234))
    block = m.render(256)
    assert np.flatnonzero(block)[0] == 123


def test_a_hit_spanning_two_blocks_is_continuous():
    m = Mixer(sample_rate=48_000, master_gain=1.0)
    m.schedule(hit(0.0, vel=127))       # full velocity so gain is 1.0
    a = m.render(64)
    b = m.render(64)
    joined = np.concatenate([a, b])
    reference = m.sample_for("snarebot-01", 38)[:128]
    assert np.allclose(joined, reference, atol=1e-6)


def test_velocity_scales_amplitude():
    loud, soft = Mixer(sample_rate=8000, master_gain=1.0), Mixer(sample_rate=8000, master_gain=1.0)
    loud.schedule(hit(0.0, vel=127))
    soft.schedule(hit(0.0, vel=40))
    assert np.max(np.abs(loud.render(4000))) > np.max(np.abs(soft.render(4000))) * 2


def test_voices_are_released_once_finished():
    m = Mixer(sample_rate=8000)
    m.schedule(hit(0.0))
    assert m.pending == 1
    m.render(8000)
    assert m.pending == 0


def test_simultaneous_voices_sum():
    one, two = Mixer(sample_rate=8000, master_gain=1.0), Mixer(sample_rate=8000, master_gain=1.0)
    one.schedule(hit(0.0, note=38))
    two.schedule(hit(0.0, note=38))
    two.schedule(hit(0.0, note=38))
    assert np.max(np.abs(two.render(2000))) > np.max(np.abs(one.render(2000)))


def test_clipping_is_counted_not_hidden():
    m = Mixer(sample_rate=8000, master_gain=1.0)
    for _ in range(20):
        m.schedule(hit(0.0))
    out = m.render(2000)
    assert m.clipped_blocks == 1
    assert np.max(np.abs(out)) <= 1.0


def test_role_comes_from_the_bound_instrument():
    model = ActuatorModel(voices=2, cycle_ms=100, accepts=frozenset({38}))
    instruments = {"b1": Instrument("b1", "snare", model)}
    m = Mixer(sample_rate=48_000, roles={k: v.role for k, v in instruments.items()})
    assert np.array_equal(m.sample_for("b1", 38), synth.snare(48_000))


def test_now_s_follows_rendered_frames():
    m = Mixer(sample_rate=1000)
    m.render(500)
    assert m.now_s == pytest.approx(0.5)


# player

def ticking(step=0.05, start=0.0):
    """A clock that advances every time it is read, so tests never wait."""
    state = {"t": start}

    def read():
        value = state["t"]
        state["t"] += step
        return value

    return read


def test_player_hands_over_every_hit():
    plan = Plan(hits=[hit(t) for t in (0.0, 0.1, 0.2)])
    t = NullTransport()
    sent = play_plan(plan, t, clock=ticking(), tail_s=0.0)
    assert sent == 3
    assert len(t.received) == 3


def test_player_sends_ahead_of_time_not_on_time():
    plan = Plan(hits=[hit(0.5)])
    t = NullTransport()
    # 0.49 is inside the default 20ms lookahead, so it goes out before it is due
    reads = iter([0.49, 0.49, 1.0, 1.0])
    play_plan(plan, t, clock=lambda: next(reads), tail_s=0.0)
    assert len(t.received) == 1


def test_player_holds_back_what_is_not_due():
    plan = Plan(hits=[hit(0.0), hit(5.0)])
    t = NullTransport()
    reads = iter([0.0, 0.0, 5.0, 5.0, 5.0])
    play_plan(plan, t, clock=lambda: next(reads), tail_s=0.0)
    assert [h.play_at_s for h in t.received] == [0.0, 5.0]


def test_a_stalled_clock_does_not_hang_for_ever(monkeypatch):
    import tutti.core.player as player_mod

    monkeypatch.setattr(player_mod, "STALL_GRACE_S", 0.05)
    monkeypatch.setattr(player_mod, "POLL_S", 0.001)
    plan = Plan(hits=[hit(0.0), hit(600.0)])
    t = NullTransport()
    play_plan(plan, t, clock=lambda: 0.0, tail_s=0.0)
    assert len(t.received) == 1


def test_empty_plan_is_a_no_op():
    assert play_plan(Plan(), NullTransport()) == 0


def test_on_hit_fires_for_each_hit():
    plan = Plan(hits=[hit(0.0), hit(0.1)])
    seen = []
    play_plan(plan, NullTransport(), on_hit=seen.append, clock=ticking(1.0), tail_s=0.0)
    assert len(seen) == 2


def test_hits_reach_the_transport_in_time_order():
    plan = Plan(hits=[hit(0.3), hit(0.1), hit(0.2)])
    t = NullTransport()
    play_plan(plan, t, clock=ticking(1.0), tail_s=0.0)
    assert [h.play_at_s for h in t.received] == [0.1, 0.2, 0.3]


# offline render

def test_render_to_wav_writes_a_playable_file(tmp_path):
    import wave

    from tutti.transports.loopback import render_to_wav

    out = tmp_path / "out.wav"
    seconds = render_to_wav([hit(0.0), hit(0.5)], out, tail_s=0.5)
    assert out.exists()
    assert seconds == pytest.approx(1.0, abs=0.01)

    with wave.open(str(out)) as f:
        assert f.getnchannels() == 1
        assert f.getsampwidth() == 2
        assert f.getframerate() == 48_000
        assert f.getnframes() == pytest.approx(48_000, abs=500)


def test_rendered_onsets_land_where_the_plan_asked(tmp_path):
    import wave

    from tutti.transports.loopback import render_to_wav

    out = tmp_path / "o.wav"
    render_to_wav([hit(0.25)], out, sample_rate=8000, tail_s=0.3)
    with wave.open(str(out)) as f:
        pcm = np.frombuffer(f.readframes(f.getnframes()), dtype="<i2")
    first = np.flatnonzero(np.abs(pcm) > 200)[0]
    assert first / 8000 == pytest.approx(0.25, abs=0.005)


def test_render_rejects_an_empty_plan(tmp_path):
    from tutti.transports.loopback import render_to_wav

    with pytest.raises(ValueError):
        render_to_wav([], tmp_path / "x.wav")
