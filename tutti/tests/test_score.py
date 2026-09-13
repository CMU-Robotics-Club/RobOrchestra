import json

import mido
import pytest

from tutti.core import Part, ScoreError, build_score, load_score
from tutti.core.score import TempoMap


def make_midi(tracks, ticks_per_beat=480):
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    for messages in tracks:
        track = mido.MidiTrack()
        for msg in messages:
            track.append(msg)
        mid.tracks.append(track)
    return mid


def note(n, t=0, vel=100, ch=0, off=False):
    kind = "note_off" if off else "note_on"
    return mido.Message(kind, note=n, velocity=0 if off else vel, channel=ch, time=t)


# tempo map

def test_default_tempo_is_120bpm():
    mid = make_midi([[note(60)]])
    tm = TempoMap.from_file(mid)
    # one beat at 120 BPM is half a second
    assert tm.seconds_at(480) == pytest.approx(0.5)


def test_tempo_change_is_piecewise():
    # 120 BPM for one beat, then 240 BPM
    mid = make_midi([[
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        mido.MetaMessage("set_tempo", tempo=250_000, time=480),
    ]])
    tm = TempoMap.from_file(mid)
    assert tm.seconds_at(480) == pytest.approx(0.5)
    # second beat runs at double speed, so it costs 0.25s not 0.5s
    assert tm.seconds_at(960) == pytest.approx(0.75)


def test_tempo_lookup_matches_a_naive_walk():
    changes = [(0, 500_000), (480, 300_000), (1440, 700_000)]
    tm = TempoMap(changes, ticks_per_beat=480)
    for tick in (0, 100, 480, 900, 1440, 5000):
        expected, prev_tick, prev_tempo = 0.0, changes[0][0], changes[0][1]
        for t, q in changes[1:]:
            if t >= tick:
                break
            expected += (t - prev_tick) * prev_tempo / 1e6 / 480
            prev_tick, prev_tempo = t, q
        expected += (tick - prev_tick) * prev_tempo / 1e6 / 480
        assert tm.seconds_at(tick) == pytest.approx(expected)


# part matching

def test_part_filters_on_track_channel_and_note():
    part = Part(part_id=1, role="snare", track=1, channel=9, notes=(38,))
    assert part.accepts(1, 9, 38)
    assert not part.accepts(0, 9, 38)
    assert not part.accepts(1, 0, 38)
    assert not part.accepts(1, 9, 45)


def test_unfiltered_part_accepts_everything():
    assert Part(part_id=1, role="any").accepts(3, 7, 100)


def test_first_matching_part_wins():
    mid = make_midi([[note(38)]])
    parts = [
        Part(part_id=1, role="snare", notes=(38,)),
        Part(part_id=2, role="also_snare", notes=(38,)),
    ]
    score = build_score(mid, parts)
    assert [e.part_id for e in score.events] == [1]


def test_unassigned_notes_are_counted_not_dropped_silently():
    mid = make_midi([[note(60), note(99, t=10)]])
    score = build_score(mid, [Part(part_id=1, role="x", notes=(60,))])
    assert len(score.events) == 1
    assert score.unassigned == 1


# octave folding, matching the Xylobot firmware

@pytest.mark.parametrize("written,expected", [(60, 60), (76, 76), (48, 60), (88, 76), (36, 60)])
def test_fold_octaves_matches_xylobot(written, expected):
    part = Part(part_id=1, role="xylo", note_range=(60, 76), fold_octaves=True)
    assert part.place(written) == expected


def test_fold_octaves_rejects_a_range_under_an_octave():
    with pytest.raises(ScoreError):
        Part(part_id=1, role="narrow", note_range=(60, 66), fold_octaves=True)


def test_range_without_folding_filters_instead_of_moving():
    part = Part(part_id=1, role="xylo", note_range=(60, 76))
    assert part.accepts(0, 0, 60)
    assert not part.accepts(0, 0, 48)


def test_transpose_applies_before_folding():
    part = Part(part_id=1, role="x", note_range=(60, 71), fold_octaves=True, transpose=12)
    assert part.place(55) == 67


# timing and duration

def test_note_times_and_durations():
    mid = make_midi([[note(38), note(38, t=480, off=True), note(38, t=480)]])
    score = build_score(mid, [Part(part_id=1, role="snare", notes=(38,))])
    assert [e.time_s for e in score.events] == pytest.approx([0.0, 1.0])
    assert score.events[0].duration_s == pytest.approx(0.5)
    assert score.events[1].duration_s is None      # never closed


def test_events_are_sorted_by_time():
    mid = make_midi([[note(60, t=960)], [note(62), note(64, t=480)]])
    parts = [Part(part_id=1, role="a", track=0), Part(part_id=2, role="b", track=1)]
    score = build_score(mid, parts)
    assert [e.time_s for e in score.events] == sorted(e.time_s for e in score.events)
    assert [e.note for e in score.events] == [62, 64, 60]


def test_zero_velocity_note_on_counts_as_note_off():
    mid = make_midi([[note(38), mido.Message("note_on", note=38, velocity=0, time=480)]])
    score = build_score(mid, [Part(part_id=1, role="snare", notes=(38,))])
    assert len(score.events) == 1
    assert score.events[0].duration_s == pytest.approx(0.5)


def test_track_index_separates_parts():
    mid = make_midi([[note(60)], [note(60, ch=1)]])
    parts = [Part(part_id=1, role="a", track=0), Part(part_id=2, role="b", track=1)]
    score = build_score(mid, parts)
    assert sorted(e.part_id for e in score.events) == [1, 2]


def test_duration_uses_tempo_at_the_time_it_ends():
    mid = make_midi([[
        mido.MetaMessage("set_tempo", tempo=500_000, time=0),
        note(38),
        mido.MetaMessage("set_tempo", tempo=250_000, time=480),
        note(38, t=480, off=True),
    ]])
    score = build_score(mid, [Part(part_id=1, role="snare", notes=(38,))])
    # first beat at 120, second at 240, so 0.5 + 0.25
    assert score.events[0].duration_s == pytest.approx(0.75)


# manifest loading

def test_load_score_from_manifest(tmp_path):
    mid = make_midi([[note(38), note(45, t=480)]])
    mid.save(tmp_path / "test.mid")
    (tmp_path / "test.json").write_text(json.dumps({
        "song": "Test",
        "midi": "test.mid",
        "parts": [
            {"part_id": 1, "role": "snare", "notes": [38]},
            {"part_id": 2, "role": "tom", "notes": [45]},
        ],
    }))
    score = load_score(tmp_path / "test.json")
    assert score.name == "Test"
    assert len(score.for_part(1)) == 1
    assert len(score.for_part(2)) == 1
    assert score.duration_s == pytest.approx(0.5)


def test_manifest_with_missing_midi_is_an_error(tmp_path):
    (tmp_path / "m.json").write_text(json.dumps({"midi": "nope.mid", "parts": [
        {"part_id": 1, "role": "x"}]}))
    with pytest.raises(ScoreError, match="does not exist"):
        load_score(tmp_path / "m.json")


def test_duplicate_part_ids_are_an_error(tmp_path):
    mid = make_midi([[note(38)]])
    mid.save(tmp_path / "t.mid")
    (tmp_path / "m.json").write_text(json.dumps({"midi": "t.mid", "parts": [
        {"part_id": 1, "role": "a"}, {"part_id": 1, "role": "b"}]}))
    with pytest.raises(ScoreError, match="duplicate"):
        load_score(tmp_path / "m.json")


def test_manifest_with_no_parts_is_an_error(tmp_path):
    mid = make_midi([[note(38)]])
    mid.save(tmp_path / "t.mid")
    (tmp_path / "m.json").write_text(json.dumps({"midi": "t.mid", "parts": []}))
    with pytest.raises(ScoreError, match="no parts"):
        load_score(tmp_path / "m.json")


def test_events_carry_their_position_in_beats():
    """Beat positions come from ticks, so they do not move when the tempo does."""
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=500_000, time=0))
    track.append(mido.Message("note_on", note=60, velocity=100, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, time=240))
    track.append(mido.MetaMessage("set_tempo", tempo=250_000, time=0))
    track.append(mido.Message("note_on", note=62, velocity=100, time=720))
    track.append(mido.Message("note_off", note=62, velocity=0, time=120))
    score = build_score(mid, [Part(part_id=1, role="xylo")])
    assert [e.beat for e in score.events] == [0.0, 2.0]
    assert score.events[1].time_s == pytest.approx(0.25 + 1.5 * 0.25)
    assert score.events[0].duration_s == pytest.approx(0.25)
