"""Jam source end to end: scripted pianist in, NullTransport hits out.

No threads, no sleeps, no devices. The harness cranks the ensemble clock by
hand and drives the same _on_note()/_tick() seam the real tick thread uses,
so what these tests exercise is exactly the production pipeline minus the
thread that paces it.
"""

import random

import pytest

from tutti.core import ActuatorModel, Instrument
from tutti.core.ensemble import Ensemble
from tutti.sources.fake_piano import bar_events
from tutti.sources.jam import JamSource
from tutti.sources.midi_in import NoteOn
from tutti.transports.loopback import NullTransport


def drum_fleet():
    return {
        "snarebot": Instrument("snarebot", "snare", ActuatorModel(
            voices=2, cycle_ms=105.0, spacing_ms=35.0,
            accepts=frozenset({37, 38, 39, 40}))),
        "tombot": Instrument("tombot", "tom", ActuatorModel(
            voices=2, cycle_ms=105.0, spacing_ms=35.0,
            accepts=frozenset({41, 43, 45, 47, 48, 50, 35, 36}))),
    }


class Harness:
    def __init__(self, meter=4, fleet=None, **kwargs):
        self.t = [0.0]
        self.transport = NullTransport()
        self.ensemble = Ensemble(fleet or drum_fleet(), self.transport,
                                 clock=lambda: self.t[0])
        self.source = JamSource(meter=meter, seed=1, **kwargs)
        self.source.bind(self.ensemble)

    def run(self, events, until_s, step=0.005):
        pending = sorted(events, key=lambda e: e.t_s)
        i = 0
        while self.t[0] <= until_s:
            while i < len(pending) and pending[i].t_s <= self.t[0]:
                self.source._on_note(pending[i])
                i += 1
            self.source._tick(self.t[0])
            self.t[0] += step


def comping(bpm=120.0, bars=8, meter=4, seed=5, start=0.5):
    rng = random.Random(seed)
    events = []
    bar_start = start
    for bar in range(bars):
        events.extend(bar_events(bar, bar_start, bpm, meter, rng))
        bar_start += meter * (60.0 / bpm)
    return events, bar_start


def test_no_lock_means_no_drums():
    rng = random.Random(99)
    t, noise = 0.5, []
    for _ in range(40):
        noise.append(NoteOn(60, 80, t))
        t += rng.uniform(0.20, 1.20)
    h = Harness()
    h.run(noise, until_s=t + 1.0)
    assert h.transport.received == []


def test_steady_comping_gets_a_groove():
    events, end = comping()
    h = Harness()
    h.run(events, until_s=end + 0.5)
    hits = h.transport.received
    assert len(hits) >= 12
    assert {hit.note for hit in hits} <= {36, 38, 45}
    for hit in hits:
        assert 1 <= hit.velocity <= 127
        if hit.note == 38:
            assert hit.bot_id == "snarebot"
        else:
            assert hit.bot_id == "tombot"


def test_hits_land_on_the_pianists_sixteenth_grid():
    events, end = comping(bpm=120.0, start=0.5)
    h = Harness()
    h.run(events, until_s=end + 0.5)
    hits = h.transport.received
    assert hits
    sixteenth = 60.0 / 120.0 / 4.0
    for hit in hits:
        offset = (hit.play_at_s - 0.5) % sixteenth
        distance = min(offset, sixteenth - offset)
        assert distance <= 0.035, f"hit at {hit.play_at_s:.3f} is {distance * 1000:.1f}ms off grid"


def test_drums_stop_soon_after_the_pianist_does():
    events, end = comping(bars=4)
    h = Harness()
    h.run(events, until_s=end + 8.0)
    last_onset = max(e.t_s for e in events)
    assert h.transport.received
    assert all(hit.play_at_s <= last_onset + 5.0 for hit in h.transport.received)


def test_the_tracker_follows_a_tempo_change():
    slow, mid = comping(bpm=120.0, bars=4)
    fast, end = comping(bpm=132.0, bars=6, seed=6, start=mid)
    h = Harness()
    h.run(slow + fast, until_s=end + 0.5)
    assert h.source.beat_state.locked
    assert h.source.beat_state.bpm == pytest.approx(132, abs=6)


def test_runtime_controls_reach_the_engine():
    h = Harness()
    h.source.set_intensity(4)
    assert h.source.intensity == 4
    h.source.set_mode("busy")
    assert h.source.mode == "busy"
    with pytest.raises(ValueError):
        h.source.set_mode("bebop")


# stage 2: listening, not just tracking

def scaled(events, factor):
    return [NoteOn(e.note, max(1, round(e.velocity * factor)), e.t_s) for e in events]


def test_soft_playing_means_quieter_sparser_drums():
    events, end = comping(bars=10)
    loud, soft = Harness(), Harness()
    loud.run(events, until_s=end + 0.5)
    soft.run(scaled(events, 0.35), until_s=end + 0.5)
    assert soft.source.intensity < loud.source.intensity
    loud_vels = [h.velocity for h in loud.transport.received[-8:]]
    soft_vels = [h.velocity for h in soft.transport.received[-8:]]
    assert sum(soft_vels) / len(soft_vels) < sum(loud_vels) / len(loud_vels)


def test_a_flurry_thins_the_mode():
    # Triplet runs: three onset clusters per beat, no chords.
    period = 60.0 / 120.0
    events = [NoteOn(60 + (k % 5), 80, 0.5 + k * period / 3) for k in range(240)]
    h = Harness()
    h.run(events, until_s=events[-1].t_s + 0.5)
    assert h.source.beat_state.locked
    assert h.source.mode == "sparse"
    assert h.source.intensity <= 2


def test_a_hole_in_the_phrase_earns_a_fill():
    period = 60.0 / 120.0
    bars_a, mid = comping(bars=6)
    bars_b, end = comping(bars=4, seed=9, start=mid)
    # Punch a two-beat hole: drop everything in the first half of bar 7.
    hole = [e for e in bars_b if not (mid - 0.02 <= e.t_s < mid + 2 * period - 0.1)]
    h = Harness()
    h.run(bars_a + hole, until_s=end + 0.5)
    assert h.source.gap_fills >= 1


def test_the_drums_fade_out_when_the_pianist_stops():
    events, end = comping(bars=6)
    h = Harness(follow=False)   # fixed intensity, so velocity changes are the fade
    h.run(events, until_s=end + 8.0)
    snares = [h_ for h_ in h.transport.received if h_.note == 38]
    assert len(snares) >= 6
    full = max(s.velocity for s in snares)
    assert snares[-1].velocity < 0.85 * full, (
        "the last snare before silence should already be fading")


def test_the_backbeat_finds_beats_two_and_four():
    # The fake pianist accents beat 1 hard (low loud root). Wherever the lock
    # lands, downbeat inference should steer the snare's backbeat onto the
    # pianist's own 2 and 4 within a few bars.
    events, end = comping(bars=16)
    h = Harness()
    h.run(events, until_s=end + 0.5)
    period = 60.0 / 120.0
    late_snares = [s for s in h.transport.received
                   if s.note == 38 and s.play_at_s > end - 4 * 4 * period]
    assert late_snares
    for s in late_snares:
        beat_pos = ((s.play_at_s - 0.5) / period) % 4
        distance = min(abs(beat_pos - 1), abs(beat_pos - 3))
        assert distance < 0.3, (
            f"snare at {s.play_at_s:.2f} sits on beat position {beat_pos:.2f}")


def test_manual_nudges_survive_the_following():
    events, end = comping(bars=12)
    midpoint = (end + 0.5) / 2
    half = [e for e in events if e.t_s < midpoint]
    rest = [e for e in events if e.t_s >= midpoint]
    h = Harness()
    h.run(half, until_s=midpoint)
    suggested = h.source.intensity
    h.source.set_intensity(min(4, suggested + 1))
    h.run(rest, until_s=end + 0.5)
    assert h.source.intensity == min(4, suggested + 1), (
        "the +1 bias should ride on top of an unchanged suggestion")


# a declared tempo

def test_with_a_declared_tempo_the_drums_play_through_a_rest():
    period = 60.0 / 100.0
    first, mid = comping(bpm=100.0, bars=6)
    rest_beats = 8
    second, end = comping(bpm=100.0, bars=4, seed=7, start=mid + rest_beats * period)
    events = first + second
    told = Harness(tempo_hint=100.0)
    untold = Harness()
    told.run(events, until_s=end + 0.5)
    untold.run(events, until_s=end + 0.5)

    def in_rest(h):
        return [x for x in h.transport.received
                if mid + 1.0 < x.play_at_s < mid + rest_beats * period - 0.2]

    told_hits, untold_hits = in_rest(told), in_rest(untold)
    assert len(told_hits) >= 8, "told the tempo, the kit keeps time through two bars of rest"
    assert len(told_hits) > len(untold_hits)
    # And at full strength: the one following by ear is fading by then.
    late_told = [x.velocity for x in told_hits if x.play_at_s > mid + 5 * period]
    late_untold = [x.velocity for x in untold_hits if x.play_at_s > mid + 5 * period]
    assert late_told and (not late_untold or max(late_untold) < max(late_told))
    assert told.source.beat_state.locked


def test_a_declared_tempo_locks_within_a_bar():
    events, end = comping(bpm=90.0, bars=8)
    told = Harness(tempo_hint=90.0)
    told.run(events, until_s=end + 0.5)
    first = min(h.play_at_s for h in told.transport.received)
    assert first < 0.5 + 6 * 60.0 / 90.0, "the first hit should land inside the second bar"
    assert told.source.beat_state.bpm == pytest.approx(90, abs=3)


# stage 3: meter

def late_snare_positions(h, end, period, meter, bars=4):
    late = [s for s in h.transport.received
            if s.note == 38 and s.play_at_s > end - bars * meter * period]
    assert late, "expected snares in the last bars"
    return [((s.play_at_s - 0.5) / period) % meter for s in late]


def test_auto_meter_hears_a_waltz_and_plays_one():
    period = 60.0 / 120.0
    events, end = comping(bars=22, meter=3)
    h = Harness(meter=4, auto_meter=True)
    h.run(events, until_s=end + 0.5)
    assert h.source.meter == 3
    assert h.source.grouping == (3,)
    assert h.source.meter_switches >= 1
    # A waltz snare sits on beat 3 of the pianist's bar.
    for pos in late_snare_positions(h, end, period, meter=3):
        assert abs(pos - 2) < 0.3, f"snare on beat position {pos:.2f}"


def test_auto_meter_hears_five_four_with_its_grouping():
    period = 60.0 / 120.0
    events, end = comping(bars=16, meter=5)
    h = Harness(meter=4, auto_meter=True)
    h.run(events, until_s=end + 0.5)
    assert h.source.meter == 5
    # The fake pianist puts the fifth on beat 3, which is two-plus-three.
    assert h.source.grouping == (2, 3)
    for pos in late_snare_positions(h, end, period, meter=5):
        assert min(abs(pos - 1), abs(pos - 4)) < 0.3, f"snare on beat position {pos:.2f}"


def test_auto_meter_leaves_four_four_alone():
    events, end = comping(bars=16, meter=4)
    h = Harness(meter=4, auto_meter=True)
    h.run(events, until_s=end + 0.5)
    assert h.source.meter == 4
    assert h.source.meter_switches == 0


def test_a_declared_grouping_shapes_the_groove():
    events, end = comping(bars=12, meter=5)
    h = Harness(meter=5, grouping=(3, 2), follow=False)
    h.run(events, until_s=end + 0.5)
    assert h.source.grouping == (3, 2)
    assert h.transport.received
    with pytest.raises(ValueError):
        JamSource(meter=5, grouping=(4, 2))


def test_two_pianists_is_a_configuration_error():
    with pytest.raises(ValueError):
        JamSource(input_port="Digital Piano", fake_bpm=100.0)


def test_a_stage_with_no_drums_is_named_not_silent():
    xylo_only = {
        "xylobot": Instrument("xylobot", "xylo", ActuatorModel(
            voices=17, cycle_ms=55.0, voice_mode="keyed", lowest_note=60,
            accepts=frozenset(range(60, 77)))),
    }
    with pytest.raises(RuntimeError, match="snare or tom"):
        Harness(fleet=xylo_only)
