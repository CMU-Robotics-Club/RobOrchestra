"""MIDI fanout for jam-along runtime."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Protocol


class MidiLikeClient(Protocol):
    def send_note_on(self, note: int, velocity_normalized: float) -> int:
        ...


@dataclass(frozen=True)
class SentNote:
    timestamp_s: float
    note: int
    velocity: int
    source: str


class MidiRouter:
    """Dispatch note events to bot output and optional mirror output."""

    def __init__(
        self,
        bot_client: MidiLikeClient | None,
        mirror_client: MidiLikeClient | None = None,
        dry_run: bool = False,
    ) -> None:
        self._bot_client = bot_client
        self._mirror_client = mirror_client
        self._dry_run = dry_run
        self._recent: deque[SentNote] = deque(maxlen=128)

    def dispatch(self, note: int, velocity: int, timestamp_s: float, source: str) -> int:
        velocity = min(max(int(velocity), 1), 127)
        normalized = velocity / 127.0

        self._recent.append(SentNote(timestamp_s=timestamp_s, note=note, velocity=velocity, source=source))
        if self._dry_run:
            return 0

        sent = 0
        if self._bot_client is not None:
            sent += int(self._bot_client.send_note_on(note, normalized))
        if self._mirror_client is not None:
            sent += int(self._mirror_client.send_note_on(note, normalized))
        return sent

    def recent_events(self) -> tuple[SentNote, ...]:
        return tuple(self._recent)
