"""Integration-style tests for jam runtime components."""

from __future__ import annotations

from jam.beat_tracker import BeatEvent
from jam.groove_engine import GrooveEngine
from jam.midi_router import MidiRouter


class _FakeMidiClient:
    def __init__(self) -> None:
        self.calls: list[tuple[int, float]] = []

    def send_note_on(self, note: int, velocity_normalized: float) -> int:
        self.calls.append((note, velocity_normalized))
        return 1


def _beat(ts: float, beat_in_bar: int, bar_index: int, bpm: float = 120.0) -> BeatEvent:
    period = 60.0 / bpm
    return BeatEvent(timestamp_s=ts, bpm=bpm, period_s=period, beat_in_bar=beat_in_bar, bar_index=bar_index)


def test_midi_router_fans_out_to_bot_and_mirror() -> None:
    bot = _FakeMidiClient()
    mirror = _FakeMidiClient()
    router = MidiRouter(bot_client=bot, mirror_client=mirror, dry_run=False)

    sent = router.dispatch(note=38, velocity=100, timestamp_s=1.0, source="groove")

    assert sent == 2
    assert len(bot.calls) == 1
    assert len(mirror.calls) == 1


def test_midi_router_dry_run_skips_send_but_records_events() -> None:
    bot = _FakeMidiClient()
    mirror = _FakeMidiClient()
    router = MidiRouter(bot_client=bot, mirror_client=mirror, dry_run=True)

    sent = router.dispatch(note=45, velocity=96, timestamp_s=2.0, source="fill")

    assert sent == 0
    assert bot.calls == []
    assert mirror.calls == []
    assert len(router.recent_events()) == 1


def test_dry_run_pipeline_emits_deterministic_fill_events() -> None:
    engine = GrooveEngine(intensity=3, mode="groove", fill_every_bars=1, fill_probability=1.0, rng_seed=42)
    router = MidiRouter(bot_client=None, mirror_client=None, dry_run=True)

    beat_times = [0.0, 0.5, 1.0, 1.5]
    for i, ts in enumerate(beat_times, start=1):
        notes = engine.notes_for_beat(_beat(ts, beat_in_bar=i, bar_index=1), confidence=0.95)
        for note in notes:
            router.dispatch(note=note.note, velocity=note.velocity, timestamp_s=note.timestamp_s, source=note.source)

    recent = router.recent_events()
    assert recent
    assert any(evt.source == "fill" for evt in recent)
