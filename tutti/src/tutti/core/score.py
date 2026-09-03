"""Turn a MIDI file plus a part manifest into timed, part-tagged note events.

The manifest is what replaces the note-number folklore in Software/Songs/README.md.
It says which track and channel belong to which part, and which notes that part
accepts, so binding a score to a robot stops depending on numbers compiled into
firmware.
"""

from __future__ import annotations

import json
from bisect import bisect_right
from dataclasses import dataclass, field
from pathlib import Path

import mido

# MIDI default when a file never sends set_tempo: 500000 us per beat = 120 BPM.
DEFAULT_TEMPO = 500_000


class ScoreError(Exception):
    pass


@dataclass(frozen=True)
class NoteEvent:
    """One note, already assigned to a part and placed on the timeline."""

    part_id: int
    note: int           # after folding and transposition, what the bot should play
    velocity: int
    time_s: float
    duration_s: float | None = None   # None if the file never sent a matching note-off
    source_note: int = 0              # what was written in the file, for debugging

    def __post_init__(self):
        if not 0 <= self.note <= 127:
            raise ScoreError(f"note {self.note} out of MIDI range on part {self.part_id}")


@dataclass(frozen=True)
class Part:
    """A line in the score and the filter that decides what belongs to it."""

    part_id: int
    role: str
    track: int | None = None
    channel: int | None = None          # 0-15, as mido reports it
    notes: tuple[int, ...] | None = None
    note_range: tuple[int, int] | None = None
    fold_octaves: bool = False
    transpose: int = 0

    def __post_init__(self):
        if self.note_range is not None:
            lo, hi = self.note_range
            if lo > hi:
                raise ScoreError(f"part {self.part_id}: note_range {lo}-{hi} is inverted")
            if self.fold_octaves and hi - lo < 11:
                raise ScoreError(
                    f"part {self.part_id}: cannot fold octaves into a range narrower "
                    f"than 12 semitones (got {lo}-{hi})"
                )

    def accepts(self, track: int, channel: int, note: int) -> bool:
        if self.track is not None and self.track != track:
            return False
        if self.channel is not None and self.channel != channel:
            return False
        if self.notes is not None:
            return note in self.notes
        if self.note_range is not None and not self.fold_octaves:
            return self.note_range[0] <= note <= self.note_range[1]
        return True

    def place(self, note: int) -> int:
        """Map a written note to the one the bot actually plays."""
        note += self.transpose
        if self.fold_octaves and self.note_range is not None:
            lo, hi = self.note_range
            # Same two loops the Xylobot firmware runs, so the software agrees
            # with the hardware about where an out-of-range note lands.
            while note < lo:
                note += 12
            while note > hi:
                note -= 12
        return note


class TempoMap:
    """Converts ticks to seconds across tempo changes.

    Precomputes the elapsed seconds at each tempo change so lookups are a
    bisect rather than a walk. Files with a tempo change per bar are common
    enough that the walk version shows up in profiles.
    """

    def __init__(self, changes: list[tuple[int, int]], ticks_per_beat: int):
        if ticks_per_beat <= 0:
            raise ScoreError("ticks_per_beat must be positive")
        self._ticks_per_beat = ticks_per_beat
        self._ticks = [t for t, _ in changes]
        self._tempos = [q for _, q in changes]

        self._seconds: list[float] = [0.0]
        for i in range(1, len(changes)):
            span = self._ticks[i] - self._ticks[i - 1]
            self._seconds.append(
                self._seconds[i - 1] + span * self._tempos[i - 1] / 1e6 / ticks_per_beat
            )

    @classmethod
    def from_file(cls, mid: mido.MidiFile) -> "TempoMap":
        changes: dict[int, int] = {}
        for track in mid.tracks:
            tick = 0
            for msg in track:
                tick += msg.time
                if msg.type == "set_tempo":
                    # Later tracks win at the same tick; MIDI files rarely
                    # disagree here, and when they do the last one is what
                    # sequencers use.
                    changes[tick] = msg.tempo
        changes.setdefault(0, DEFAULT_TEMPO)
        ordered = sorted(changes.items())
        return cls(ordered, mid.ticks_per_beat)

    def seconds_at(self, tick: int) -> float:
        i = bisect_right(self._ticks, tick) - 1
        span = tick - self._ticks[i]
        return self._seconds[i] + span * self._tempos[i] / 1e6 / self._ticks_per_beat

    def tempo_at(self, tick: int) -> int:
        return self._tempos[bisect_right(self._ticks, tick) - 1]

    @property
    def initial_bpm(self) -> float:
        return 60_000_000 / self._tempos[0]


@dataclass
class Score:
    name: str
    events: list[NoteEvent] = field(default_factory=list)
    parts: list[Part] = field(default_factory=list)
    unassigned: int = 0     # notes no part claimed, useful for catching a bad manifest
    initial_bpm: float = 120.0

    @property
    def duration_s(self) -> float:
        return max((e.time_s for e in self.events), default=0.0)

    def for_part(self, part_id: int) -> list[NoteEvent]:
        return [e for e in self.events if e.part_id == part_id]


def parse_parts(raw: list[dict]) -> list[Part]:
    parts = []
    seen = set()
    for entry in raw:
        try:
            part_id = int(entry["part_id"])
            role = str(entry["role"])
        except KeyError as exc:
            raise ScoreError(f"part entry missing {exc}") from exc
        if part_id in seen:
            raise ScoreError(f"duplicate part_id {part_id}")
        seen.add(part_id)

        notes = entry.get("notes")
        note_range = entry.get("note_range")
        parts.append(
            Part(
                part_id=part_id,
                role=role,
                track=entry.get("track"),
                channel=entry.get("channel"),
                notes=tuple(notes) if notes else None,
                note_range=tuple(note_range) if note_range else None,
                fold_octaves=bool(entry.get("fold_octaves", False)),
                transpose=int(entry.get("transpose", 0)),
            )
        )
    if not parts:
        raise ScoreError("manifest declares no parts")
    return parts


def load_score(manifest_path: str | Path) -> Score:
    """Read a manifest and the MIDI file it names."""
    manifest_path = Path(manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        raise ScoreError(f"{manifest_path}: {exc}") from exc

    midi_path = manifest_path.parent / manifest["midi"]
    if not midi_path.exists():
        raise ScoreError(f"manifest names {midi_path}, which does not exist")

    parts = parse_parts(manifest.get("parts", []))
    mid = mido.MidiFile(midi_path)
    return build_score(mid, parts, name=manifest.get("song", midi_path.stem))


def build_score(mid: mido.MidiFile, parts: list[Part], name: str = "") -> Score:
    """Walk every track, assign each note to a part, and place it in seconds.

    Tracks are walked separately rather than merged because the track index is
    part of how a part is identified, and merging throws it away.
    """
    tempo_map = TempoMap.from_file(mid)
    score = Score(name=name, parts=list(parts), initial_bpm=tempo_map.initial_bpm)

    for track_index, track in enumerate(mid.tracks):
        tick = 0
        # (channel, note) -> index into score.events, so note-off can fill in duration
        open_notes: dict[tuple[int, int], int] = {}

        for msg in track:
            tick += msg.time
            if msg.type not in ("note_on", "note_off"):
                continue

            is_on = msg.type == "note_on" and msg.velocity > 0
            key = (msg.channel, msg.note)

            if is_on:
                part = _first_match(parts, track_index, msg.channel, msg.note)
                if part is None:
                    score.unassigned += 1
                    continue
                score.events.append(
                    NoteEvent(
                        part_id=part.part_id,
                        note=part.place(msg.note),
                        velocity=msg.velocity,
                        time_s=tempo_map.seconds_at(tick),
                        source_note=msg.note,
                    )
                )
                open_notes[key] = len(score.events) - 1
            else:
                index = open_notes.pop(key, None)
                if index is None:
                    continue
                started = score.events[index]
                score.events[index] = NoteEvent(
                    part_id=started.part_id,
                    note=started.note,
                    velocity=started.velocity,
                    time_s=started.time_s,
                    duration_s=tempo_map.seconds_at(tick) - started.time_s,
                    source_note=started.source_note,
                )

    score.events.sort(key=lambda e: (e.time_s, e.part_id, e.note))
    return score


def _first_match(parts: list[Part], track: int, channel: int, note: int) -> Part | None:
    for part in parts:
        if part.accepts(track, channel, note):
            return part
    return None
