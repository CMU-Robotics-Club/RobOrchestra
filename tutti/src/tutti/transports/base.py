"""What every way of reaching the bots has in common.

A transport takes hits that are already scheduled and gets them to whatever
plays them. It is handed each hit early, by the lookahead, and is responsible
for making the sound happen at play_at_s rather than on arrival. That is the
whole point of the design: nothing downstream should ever have to guess when a
note was meant to land.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from ..core.plan import ScheduledHit


class Transport(ABC):
    """Base for every way of reaching the bots."""

    name = "transport"

    @abstractmethod
    def send(self, hits: Iterable[ScheduledHit]) -> int:
        """Hand over hits due soon. Returns how many were accepted."""

    def start(self) -> None:
        """Called once before the first send."""

    def close(self) -> None:
        """Release anything held. Must be safe to call twice."""

    @property
    def lookahead_s(self) -> float:
        """How far ahead of play_at_s this transport needs its hits.

        Sized by the worst case of the link underneath: near zero in process,
        60 ms over wifi, 120 ms over BLE.
        """
        return 0.0

    def live_lead_s(self, bot_id: str) -> float:
        """Earliest honest play_at for a strike requested right now.

        Scored playback plans far ahead, so it never asks this. A live source
        cannot: when a hand comes down the hit has to be scheduled at the
        soonest moment the transport can still honour, and stamping it any
        earlier just gets it reported late. Defaults to lookahead_s.
        """
        return self.lookahead_s

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.close()
        return False
