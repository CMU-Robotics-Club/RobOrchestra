"""Recorded P-45 sessions, replayed through the pipeline as regression fixtures.

Everything else in the suite is synthesised. These are real hands on a real
keyboard, captured with `tutti jam --record`, and what the tracker does with
them is the only measure that finally counts. Each fixture states what was
played and what a listening drummer should have done with it; a change to
the tracker that moves these numbers has to justify itself here.
"""

from pathlib import Path

from tutti.sources.jam import load_session
from tutti.sources.replay import replay_session

SESSIONS = Path(__file__).parent / "sessions"


def test_a_chromatic_run_is_a_pulse_and_free_playing_is_not():
    # A descending chromatic run, one note every ~200 ms with no accents, for
    # eight seconds; then two-note figures at irregular gaps with pauses of
    # up to three seconds. The run has no beat-level onsets at all, only
    # subdivisions, but it is perfectly even: a drummer would take it. The
    # free playing after it is not a pulse and must not be treated as one
    # by the end.
    events = load_session(str(SESSIONS / "p45_chromatic_run_then_free.jsonl"))
    replay = replay_session(events, seed=1)

    assert replay.first_lock_s is not None and replay.first_lock_s < 7.0
    during_run = [s for s in replay.snapshots if 6.0 <= s.t_s <= 10.0]
    assert during_run and all(s.locked for s in during_run)
    assert all(s.bpm is not None and 95 <= s.bpm <= 105 for s in during_run), (
        "the run reads as 100 BPM: three notes per beat")

    tail = [s for s in replay.snapshots if s.t_s >= 30.0]
    assert tail and not any(s.locked for s in tail)


def test_a_metronomic_ballad_tempo_locks_fast_and_holds():
    # The same triad on every beat at 66 BPM, metronomic to ±20 ms, for
    # fourteen seconds; then the same at ~140, then at ~230 chords a minute.
    # The first segment is the plainest possible pulse and sits below the
    # old 70 BPM floor, which is why it is here: a ballad must be in range.
    # The later segments are a change of tempo the tracker should follow.
    events = load_session(str(SESSIONS / "p45_metronome_66_then_140_then_230.jsonl"))
    replay = replay_session(events, seed=1)

    assert replay.first_lock_s is not None and replay.first_lock_s < 7.0
    ballad = [s for s in replay.snapshots if 6.0 <= s.t_s <= 14.0]
    assert ballad and all(s.locked for s in ballad)
    assert all(s.bpm is not None and 62 <= s.bpm <= 70 for s in ballad)
    assert all(s.confidence >= 0.9 for s in ballad)
    assert replay.locked_fraction >= 0.6


def test_an_accelerando_a_soft_passage_a_hole_and_a_stop():
    # Chords on every beat at 92, speeding up steadily to 150 over fifteen
    # seconds; then the same but softer (velocities in the twenties instead
    # of the forties); then a hole; then a stop and a restart at double
    # speed. A listening drummer locks fast, follows the accelerando rather
    # than fighting it, hushes for the soft passage, fills the hole, and
    # fades during the stop.
    events = load_session(str(SESSIONS / "p45_accelerando_soft_hole_stop.jsonl"))
    replay = replay_session(events, seed=1)

    assert replay.first_lock_s is not None and replay.first_lock_s < 6.0
    early = [s for s in replay.snapshots if 5.0 <= s.t_s <= 7.0]
    assert early and all(85 <= s.bpm <= 100 for s in early)
    settled = [s for s in replay.snapshots if 20.0 <= s.t_s <= 24.0]
    assert settled and all(s.locked and 140 <= s.bpm <= 160 for s in settled)

    normal = [s.intensity for s in replay.snapshots if 8.0 <= s.t_s <= 18.0]
    soft = [s.intensity for s in replay.snapshots if 21.0 <= s.t_s <= 25.0]
    assert min(soft) < max(normal), "the soft passage should hush the drums"

    assert any(s.gap_fills >= 1 for s in replay.snapshots if s.t_s <= 30.0)
    assert any(s.velocity_scale < 1.0 for s in replay.snapshots if 24.0 <= s.t_s <= 34.0)
    assert replay.locked_fraction >= 0.75


def test_a_waltz_is_heard_as_one_and_the_drums_sit_on_its_bars():
    # A waltz at about 136: a bass note on beat 1, chords on 2 and 3, for
    # forty seconds, drifting a few percent either way. Declared 4/4 with
    # meter detection on, the tracker must find 3/4 within a few bars, and
    # the groove must then sit on the pianist's own bars: kicks on the bass
    # notes, snares on beat 3.
    events = load_session(str(SESSIONS / "p45_waltz_136.jsonl"))
    replay = replay_session(events, seed=1, meter=4, auto_meter=True)

    assert replay.first_lock_s is not None and replay.first_lock_s < 5.0
    assert replay.locked_fraction >= 0.85

    # The pianist's bars, from the bass notes.
    clusters: list[tuple[float, int]] = []
    for e in events:
        if clusters and e.t_s - clusters[-1][0] < 0.05:
            clusters[-1] = (clusters[-1][0], min(clusters[-1][1], e.note))
        else:
            clusters.append((e.t_s, e.note))
    bars = [t for t, low in clusters if low < 52]
    assert len(bars) >= 20

    def beat_in_bar(t: float) -> float | None:
        before = [b for b in bars if b <= t + 0.05]
        after = [b for b in bars if b > t + 0.05]
        if not before or not after:
            return None
        return 3.0 * (t - before[-1]) / (after[0] - before[-1])

    late = [h for h in replay.hits if h.play_at_s > 20.0]
    loudest = max(h.velocity for h in late if h.note == 38)
    backbeats = [beat_in_bar(h.play_at_s) for h in late
                 if h.note == 38 and h.velocity >= 0.7 * loudest]     # not the ghosts
    backbeats = [s for s in backbeats if s is not None]
    assert len(backbeats) >= 8
    on_answer = [s for s in backbeats if min(abs(s - 2.0), abs(s - 1.0)) < 0.35]
    # Fills at phrase ends put a snare or two elsewhere; the rest sit on the bar.
    assert len(on_answer) >= 0.8 * len(backbeats), (
        f"snares should sit on beat 3 (or 2) of the pianist's bar, got "
        f"{sorted(round(s, 2) for s in backbeats)}")
    assert sum(1 for s in backbeats if abs(s - 2.0) < 0.35) >= 8, "beat 3 is the waltz's answer"
    kicks = [beat_in_bar(h.play_at_s) for h in late if h.note == 36]
    kicks = [k for k in kicks if k is not None]
    on_the_bass = [k for k in kicks if k < 0.35 or k > 2.65]
    assert len(on_the_bass) >= 5, "kicks should land on the bass notes"


def test_swing_reads_as_the_beat_and_stays_in_groove():
    # Swung eighths at about 105-115, a 2:1 triplet feel: the "and" sits at
    # two thirds of the beat, wandering between 0.60 and 0.75. The tempo
    # must be the beat, never the long eighth (which would read as ~165),
    # the lock must hold through the swing, and two onsets a beat is
    # comping, not a flurry — the drums stay in groove.
    events = load_session(str(SESSIONS / "p45_swing_105.jsonl"))
    replay = replay_session(events, seed=1)

    assert replay.first_lock_s is not None and replay.first_lock_s < 10.0
    settled = [s for s in replay.snapshots if s.t_s >= 10.0]
    locked = [s for s in settled if s.locked]
    assert len(locked) >= 0.7 * len(settled)
    assert all(95 <= s.bpm <= 125 for s in locked), (
        f"tempi seen: {sorted({round(s.bpm) for s in locked})}")
    assert sum(1 for s in locked if s.mode == "groove") >= 0.7 * len(locked)
    assert not any(s.gap_fills for s in replay.snapshots if s.t_s < replay.first_lock_s)


def test_a_whole_song_told_its_tempo_is_accompanied_throughout():
    # Three minutes of a real piece at about 72, played softly with rests,
    # rubato and section changes, with the tempo declared. The drummer comes
    # in on the count, stays with the piece, hears its sections and chords,
    # and fills its holes.
    events = load_session(str(SESSIONS / "p45_song_told_72.jsonl"))
    replay = replay_session(events, seed=1, tempo_hint=72.0)

    assert replay.first_lock_s is not None and replay.first_lock_s < 3.0
    assert replay.locked_fraction >= 0.85
    assert len(replay.hits) >= 200
    late = [s for s in replay.snapshots if s.t_s > 60.0]
    assert max(s.section for s in late) >= 2, "a whole song has more than one section"
    assert any(s.gap_fills >= 1 for s in late)     # a real hole is answered; hesitations are not
    named = [s for s in late if s.locked]
    assert sum(1 for s in named if s.chord) >= 0.9 * len(named), "chords are named while locked"
    assert all(0.05 <= s.activity <= 1.0 for s in named)
    assert sum(1 for s in named if s.activity > 0.1) >= 0.7 * len(named), (
        "soft, busy playing should thin the drums, not silence them")


def test_a_wrong_tempo_hint_yields_to_what_is_actually_played():
    # An oom-pah accompaniment: bass on the beat at about 96, chords on the
    # "and", 190 onsets a minute. The pianist declared 130, a tempo the
    # playing does not contain at any octave. A 3:2 misfit grid can be laid
    # over it — every third onset lands, the rest sit on the grid's triplets
    # — and that is exactly what must not happen: the evidence for 96 is
    # unrelated to the hint and far stronger, and it wins.
    events = load_session(str(SESSIONS / "p45_oom_pah_96_told_130.jsonl"))
    for hint in (None, 90.0, 130.0):
        replay = replay_session(events, seed=1, tempo_hint=hint)
        assert replay.first_lock_s is not None and replay.first_lock_s < 4.0, hint
        settled = [s for s in replay.snapshots if 8.0 <= s.t_s <= 26.0]
        locked = [s for s in settled if s.locked]
        assert len(locked) >= 0.8 * len(settled), hint
        assert all(90 <= s.bpm <= 104 for s in locked), (
            f"told {hint}: tempi seen {sorted({round(s.bpm) for s in locked})}")


def test_a_fast_waltz_declared_in_three_sits_on_its_bars():
    # The Up theme played as a fast waltz: oom-pah-pah, quarter notes at
    # about 190, a bass note opening every bar. By ear the tracker reads
    # this in two at 95 — half the quarter rate, which cannot divide a
    # three-beat bar — and its downbeat lands on the bass only every third
    # bar. Declared in three at 190 it must lock on the count, hold, and
    # put the kick on the pianist's bass notes.
    events = load_session(str(SESSIONS / "p45_fast_waltz_190.jsonl"))
    replay = replay_session(events, seed=1, meter=3, tempo_hint=190.0)
    assert replay.first_lock_s is not None and replay.first_lock_s < 2.0
    assert replay.locked_fraction >= 0.9
    assert all(178 <= s.bpm <= 200 for s in replay.snapshots if s.locked and s.t_s > 5.0)

    clusters: list[tuple[float, int]] = []
    for e in events:
        if clusters and e.t_s - clusters[-1][0] < 0.05:
            clusters[-1] = (clusters[-1][0], min(clusters[-1][1], e.note))
        else:
            clusters.append((e.t_s, e.note))
    bass = [t for t, low in clusters if low < 52]
    bars = [b for a, b in zip(bass, bass[1:]) if 0.8 < b - a < 1.1]   # oom-pah-pah bars
    assert len(bars) >= 12
    kicks = [h.play_at_s for h in replay.hits if h.note == 36]
    on_bar = sum(1 for b in bars if any(abs(k - b) < 0.07 for k in kicks))
    assert on_bar >= 0.85 * len(bars), f"kick on {on_bar} of {len(bars)} bars"
    # The bass alternates F and C for four bars at a time; a chord change
    # held for a phrase is not a new section.
    assert max(s.section for s in replay.snapshots) <= 1


def test_a_ritardando_is_followed_all_the_way_down():
    # Chords on every beat at 121 for fifteen seconds, then a gradual
    # ritardando over fifteen more, down to about 81. The grid must bend
    # with the playing rather than run ahead of it: the lock holds, the
    # tempo reading tracks the slowdown, and the snare stays as close to the
    # pianist's chords while slowing as it was while steady.
    events = load_session(str(SESSIONS / "p45_ritardando_121_to_84.jsonl"))
    replay = replay_session(events, seed=1)

    assert replay.first_lock_s is not None and replay.first_lock_s < 6.0
    assert replay.locked_fraction >= 0.85
    steady = [s for s in replay.snapshots if 8.0 <= s.t_s <= 15.0]
    assert steady and all(s.locked and 112 <= s.bpm <= 130 for s in steady)
    slowed = [s for s in replay.snapshots if 28.0 <= s.t_s <= 32.0]
    assert slowed and all(s.locked and s.bpm <= 95 for s in slowed)
    assert any(s.rubato > 1.03 for s in replay.snapshots if 16.0 <= s.t_s <= 30.0)

    chords: list[float] = []
    for e in events:
        if not chords or e.t_s - chords[-1] >= 0.05:
            chords.append(e.t_s)

    def distance_ms(t: float) -> float:
        return min(abs(t - c) for c in chords) * 1000.0

    def median_snare_distance(lo: float, hi: float) -> float:
        d = sorted(distance_ms(h.play_at_s) for h in replay.hits
                   if h.note == 38 and lo <= h.play_at_s < hi)
        assert len(d) >= 6
        return d[len(d) // 2]

    assert median_snare_distance(8.0, 18.0) < 40.0
    assert median_snare_distance(18.0, 32.0) < 40.0
