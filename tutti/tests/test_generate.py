"""The generative groove, judged on the properties a drummer would check."""

import pytest

from tutti.core.generate import KICK, SNARE, TOM, BeatContext, GrooveGenerator, slot_probabilities


def bars(gen, n, activity=0.5, beats_per_bar=4, bpm=120.0, **extra):
    """Generate n bars; return a list of per-bar lists of (beat, sub, note)."""
    period = 60.0 / bpm
    out = []
    t = 10.0
    for bar in range(n):
        hits = []
        for beat in range(1, beats_per_bar + 1):
            ctx = BeatContext(time_s=t, period_s=period, beat_in_bar=beat, bar_index=bar,
                              activity=activity, **extra)
            for note in gen.notes_for_beat(ctx):
                sub = round((note.time_s - t) / (period / 4.0), 2)
                hits.append((beat, sub, note.note, note.velocity))
            t += period
        out.append(hits)
    return out


def test_the_backbone_is_never_negotiable():
    for activity in (0.0, 0.5, 1.0):
        gen = GrooveGenerator(rng_seed=3)
        for hits in bars(gen, 12, activity=activity):
            on_beat = {(b, n) for b, s, n, _ in hits if s == 0}
            assert (1, KICK) in on_beat
            assert (2, SNARE) in on_beat and (4, SNARE) in on_beat


def test_activity_buys_decoration():
    def mean_hits(activity):
        gen = GrooveGenerator(rng_seed=5, decoration=1.0)
        played = bars(gen, 32, activity=activity)
        return sum(len(h) for h in played) / len(played)

    quiet, mid, busy = mean_hits(0.05), mean_hits(0.5), mean_hits(1.0)
    assert quiet < mid < busy
    assert busy >= quiet + 3


def test_decoration_zero_is_the_plain_beat():
    gen = GrooveGenerator(rng_seed=3, decoration=0.0)
    for hits in bars(gen, 12, activity=1.0):
        assert all(s == 0 for _, s, _, _ in hits), "nothing off the beat"
        assert {(b, n) for b, _, n, _ in hits} <= {(1, KICK), (3, KICK), (2, SNARE), (4, SNARE)}


def test_decoration_scales_the_optional_playing():
    def mean_hits(decoration):
        gen = GrooveGenerator(rng_seed=5, decoration=decoration)
        played = bars(gen, 32, activity=0.8)
        return sum(len(h) for h in played) / len(played)

    assert mean_hits(0.0) < mean_hits(0.5) < mean_hits(1.0)


def test_riffs_decide_where_the_fills_go():
    def fill_notes(riffs, requested=False, **ctx):
        gen = GrooveGenerator(rng_seed=2, riffs=riffs)
        bars(gen, 2)
        if requested:
            gen.request_fill()
        period, t, out = 0.5, 20.0, []
        for beat in range(1, 5):
            c = BeatContext(time_s=t, period_s=period, beat_in_bar=beat, bar_index=5, **ctx)
            out += [n for n in gen.notes_for_beat(c) if n.source == "fill"]
            t += period
        return out

    assert fill_notes("phrase", phrase_end=True)
    assert not fill_notes("period", phrase_end=True)
    assert fill_notes("period", phrase_end=True, hyper_end=True)
    assert not fill_notes("none", phrase_end=True, hyper_end=True)
    assert fill_notes("none", requested=True), "the fill command still works"
    with pytest.raises(ValueError):
        GrooveGenerator(riffs="sometimes")


def test_mutation_zero_repeats_the_bar():
    gen = GrooveGenerator(rng_seed=8, mutation=0.0, decoration=1.0)
    played = bars(gen, 8, activity=0.6)
    shapes = {tuple(sorted((b, s, n) for b, s, n, _ in h)) for h in played}
    assert len(shapes) == 1


def test_bars_vary_but_keep_their_identity():
    gen = GrooveGenerator(rng_seed=8)
    played = bars(gen, 16, activity=0.6)
    shapes = {tuple(sorted((b, s, n) for b, s, n, _ in h)) for h in played}
    assert len(shapes) >= 4, "a generative groove should not repeat one bar"
    for a, b in zip(played, played[1:]):
        sa = {(x, y, z) for x, y, z, _ in a}
        sb = {(x, y, z) for x, y, z, _ in b}
        assert len(sa & sb) >= 0.5 * min(len(sa), len(sb)), "consecutive bars should be kin"


def test_same_seed_same_groove():
    a = bars(GrooveGenerator(rng_seed=11), 8, activity=0.7)
    b = bars(GrooveGenerator(rng_seed=11), 8, activity=0.7)
    assert a == b


def test_gain_scales_every_velocity():
    loud = bars(GrooveGenerator(rng_seed=2), 4, activity=0.5, gain=1.2)
    soft = bars(GrooveGenerator(rng_seed=2), 4, activity=0.5, gain=0.6)
    for lb, sb in zip(loud, soft):
        for (_, _, _, lv), (_, _, _, sv) in zip(lb, sb):
            assert sv < lv


def test_the_pianists_accented_beat_is_accented():
    plain = bars(GrooveGenerator(rng_seed=2), 4, activity=0.3)
    accented = bars(GrooveGenerator(rng_seed=2), 4, activity=0.3, accent=1.2)
    plain_kick = next(v for b, s, n, v in plain[0] if b == 1 and s == 0 and n == KICK)
    accented_kick = next(v for b, s, n, v in accented[0] if b == 1 and s == 0 and n == KICK)
    assert accented_kick > plain_kick


def test_swing_moves_the_offbeats_and_drops_the_sixteenths():
    gen = GrooveGenerator(rng_seed=4)
    played = bars(gen, 16, activity=1.0, swing=0.67)
    subs = {s for h in played for _, s, _, _ in h}
    assert 2.68 in subs or any(2.6 <= s <= 2.75 for s in subs), "the and sits at two thirds"
    assert not any(0.5 <= s <= 1.5 or 2.9 <= s <= 3.2 for s in subs), "no straight sixteenths in a swing feel"


def test_a_phrase_end_carries_a_fill_and_a_period_end_a_bigger_one():
    def last_beat_hits(**extra):
        gen = GrooveGenerator(rng_seed=6)
        played = bars(gen, 6, activity=0.5, **extra)
        return [sum(1 for b, _, _, _ in h if b == 4) for h in played]

    plain = last_beat_hits()
    phrase = last_beat_hits(phrase_end=True)
    period = last_beat_hits(hyper_end=True)
    assert sum(phrase) > sum(plain)
    assert sum(period) >= sum(phrase)


def test_a_fill_can_answer_the_pianists_rhythm():
    gen = GrooveGenerator(rng_seed=6)
    # The pianist's last bar had onsets on sixteenths 12, 13 and 15 (beat 4).
    played = bars(gen, 1, activity=0.5, phrase_end=True, echo=(12, 13, 15))
    last = sorted((s, n) for b, s, n, _ in played[0] if b == 4 and n in (SNARE, TOM))
    assert [s for s, _ in last] == [0.0, 1.0, 3.0]


def test_a_new_section_opens_with_an_accent():
    gen = GrooveGenerator(rng_seed=6)
    played = bars(gen, 1, activity=0.2, section_started=True)
    downbeat = {(n, v) for b, s, n, v in played[0] if b == 1 and s == 0}
    assert any(n == TOM for n, _ in downbeat)
    assert any(n == SNARE and v > 100 for n, v in downbeat)


def test_an_expected_chord_change_gets_a_kick():
    gen = GrooveGenerator(rng_seed=6)
    plain = bars(gen, 8, activity=0.0)
    kicks_on_two = sum(1 for h in plain for b, s, n, _ in h if b == 2 and s == 0 and n == KICK)
    assert kicks_on_two == 0
    gen = GrooveGenerator(rng_seed=6, decoration=1.0)
    changing = bars(gen, 8, activity=0.0, chord_change=True)
    kicks_on_two = sum(1 for h in changing for b, s, n, _ in h if b == 2 and s == 0 and n == KICK)
    assert kicks_on_two == 8
    # It is decoration: the plain beat does not mark harmony.
    gen = GrooveGenerator(rng_seed=6, decoration=0.0)
    plain = bars(gen, 8, activity=0.0, chord_change=True)
    assert sum(1 for h in plain for b, s, n, _ in h if b == 2 and s == 0 and n == KICK) == 0


def test_other_meters_keep_their_own_backbone():
    waltz = bars(GrooveGenerator(beats_per_bar=3, rng_seed=1), 8, beats_per_bar=3)
    for hits in waltz:
        on_beat = {(b, n) for b, s, n, _ in hits if s == 0}
        assert (1, KICK) in on_beat and (3, SNARE) in on_beat
        assert (2, KICK) not in on_beat
    five = bars(GrooveGenerator(beats_per_bar=5, grouping=(3, 2), rng_seed=1), 8, beats_per_bar=5)
    for hits in five:
        on_beat = {(b, n) for b, s, n, _ in hits if s == 0}
        assert (1, KICK) in on_beat and (4, KICK) in on_beat
        assert (3, SNARE) in on_beat and (5, SNARE) in on_beat


def test_physical_floors_are_respected():
    gen = GrooveGenerator(rng_seed=9, kt_min_gap_s=0.3)
    period = 60.0 / 120.0
    times = []
    t = 10.0
    for bar in range(8):
        for beat in range(1, 5):
            ctx = BeatContext(time_s=t, period_s=period, beat_in_bar=beat, bar_index=bar,
                              activity=1.0)
            times += [n.time_s for n in gen.notes_for_beat(ctx) if n.note in (KICK, TOM)]
            t += period
    times.sort()
    for a, b in zip(times, times[1:]):
        assert b - a >= 0.3 - 1e-9
    assert gen.thinned > 0


def test_slot_probabilities_have_the_backbone_at_one():
    probs = slot_probabilities((4,), 0.5)
    assert probs[(0, 0, "K")] == 1.0 and probs[(1, 0, "S")] == 1.0 and probs[(3, 0, "S")] == 1.0
    assert 0.0 < probs[(3, 2, "K")] < 1.0
    assert slot_probabilities((4,), 1.0)[(3, 2, "K")] > probs[(3, 2, "K")]
