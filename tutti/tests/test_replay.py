"""Recording a session and replaying it through the pipeline offline."""

import random

from tutti.sources.fake_piano import bar_events
from tutti.sources.jam import load_session, save_session
from tutti.sources.midi_in import NoteOn
from tutti.sources.replay import describe, replay_session


def comping(bpm=120.0, bars=12, meter=4, seed=5, start=0.5):
    rng = random.Random(seed)
    events, bar_start = [], start
    for bar in range(bars):
        events.extend(bar_events(bar, bar_start, bpm, meter, rng))
        bar_start += meter * (60.0 / bpm)
    return events


def test_a_session_survives_the_round_trip(tmp_path):
    events = comping(bars=2)
    path = tmp_path / "session.jsonl"
    save_session(str(path), events)
    back = load_session(str(path))
    assert len(back) == len(events)
    assert back[0].t_s == 0.0                       # times start at zero
    assert [e.note for e in back] == [e.note for e in events]
    assert [e.velocity for e in back] == [e.velocity for e in events]
    spans = [round(e.t_s - events[0].t_s, 4) for e in events]
    assert [e.t_s for e in back] == spans


def test_replaying_comping_locks_and_plays():
    replay = replay_session(comping(bars=12), seed=1)
    assert replay.events > 0
    assert replay.first_lock_s is not None
    assert replay.first_lock_s < 8.0
    assert replay.locked_fraction > 0.6
    assert len(replay.hits) >= 20
    lines = describe(replay)
    assert lines[-1].startswith(f"{replay.events} notes")
    assert any("lock=Y" in line for line in lines)


def test_replaying_silence_reports_never():
    replay = replay_session([NoteOn(60, 80, 0.5), NoteOn(64, 80, 3.0)], seed=1)
    assert replay.first_lock_s is None
    assert replay.hits == []
    assert describe(replay)[-1].endswith("first lock never, locked 0% of the time, 0 hits")
