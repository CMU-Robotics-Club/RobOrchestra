"""Rule-based groove and fill scheduling."""

from __future__ import annotations

import random
from dataclasses import dataclass

from .beat_tracker import BeatEvent

_NOTE_MAP = {
    "K": 36,  # kick (TomBot route)
    "S": 38,  # snare
    "T": 45,  # tom
}

_MODE_SET = {"groove", "sparse", "busy"}


@dataclass(frozen=True)
class ScheduledNote:
    """Note scheduled on the beat grid."""

    timestamp_s: float
    note: int
    velocity: int
    source: str


class GrooveEngine:
    """Generate drum notes from beat pulses."""

    def __init__(
        self,
        intensity: int = 2,
        mode: str = "groove",
        fill_every_bars: int = 8,
        fill_probability: float = 0.30,
        rng_seed: int | None = None,
    ) -> None:
        self._intensity = 0
        self._mode = "groove"
        self.set_intensity(intensity)
        self.set_mode(mode)

        self._fill_every_bars = max(int(fill_every_bars), 1)
        self._fill_probability = min(max(float(fill_probability), 0.0), 1.0)

        self._rng = random.Random(rng_seed)
        self._force_fill_next_bar = False
        self._active_fill_bar: int | None = None

    @property
    def intensity(self) -> int:
        return self._intensity

    @property
    def mode(self) -> str:
        return self._mode

    def set_intensity(self, value: int) -> None:
        self._intensity = min(max(int(value), 0), 4)

    def set_mode(self, value: str) -> None:
        lowered = str(value).strip().lower()
        if lowered not in _MODE_SET:
            raise ValueError(f"Unknown mode: {value}")
        self._mode = lowered

    def request_fill(self) -> None:
        self._force_fill_next_bar = True

    def notes_for_beat(self, beat_event: BeatEvent, confidence: float) -> list[ScheduledNote]:
        confidence = float(confidence)

        if beat_event.beat_in_bar == 1:
            self._roll_fill_decision(beat_event.bar_index, confidence)

        use_fill = (
            self._active_fill_bar == beat_event.bar_index
            and beat_event.beat_in_bar == 4
            and confidence >= 0.60
        )

        start_step = (beat_event.beat_in_bar - 1) * 4
        step_tokens = self._fill_tokens() if use_fill else self._pattern_tokens()

        notes: list[ScheduledNote] = []
        substep_s = beat_event.period_s / 4.0
        for local_step in range(4):
            step = start_step + local_step
            token = step_tokens[step]
            if token is None:
                continue
            note = _NOTE_MAP[token]
            velocity = self._velocity_for(token)
            timestamp_s = beat_event.timestamp_s + local_step * substep_s
            notes.append(
                ScheduledNote(
                    timestamp_s=timestamp_s,
                    note=note,
                    velocity=velocity,
                    source="fill" if use_fill else "groove",
                )
            )
        return notes

    def _roll_fill_decision(self, bar_index: int, confidence: float) -> None:
        if confidence < 0.60:
            self._active_fill_bar = None
            self._force_fill_next_bar = False
            return

        should_fill = False
        if self._force_fill_next_bar:
            should_fill = True
            self._force_fill_next_bar = False
        elif bar_index > 0 and (bar_index % self._fill_every_bars) == 0:
            should_fill = self._rng.random() <= self._fill_probability

        self._active_fill_bar = bar_index if should_fill else None

    def _pattern_tokens(self) -> list[str | None]:
        pattern: list[str | None] = [None] * 16

        if self._mode == "sparse":
            for step, tok in ((0, "K"), (4, "S"), (8, "K"), (12, "S")):
                pattern[step] = tok
            if self._intensity >= 3:
                pattern[10] = "K"

        elif self._mode == "busy":
            for step, tok in ((0, "K"), (3, "T"), (4, "S"), (6, "K"), (8, "K"), (11, "T"), (12, "S"), (14, "K")):
                pattern[step] = tok
            if self._intensity <= 1:
                pattern[3] = None
                pattern[11] = None
            if self._intensity >= 3:
                pattern[15] = "T"

        else:  # groove
            for step, tok in ((0, "K"), (4, "S"), (8, "K"), (10, "K"), (12, "S")):
                pattern[step] = tok
            if self._intensity <= 1:
                pattern[10] = None
            if self._intensity >= 3:
                pattern[15] = "T"

        if self._intensity == 0:
            for i in range(16):
                if i not in (0, 4, 8, 12):
                    pattern[i] = None

        return pattern

    def _fill_tokens(self) -> list[str | None]:
        pattern = self._pattern_tokens()

        if self._intensity <= 1:
            fill = ["S", None, "T", "S"]
        elif self._intensity == 2:
            fill = ["S", "T", "S", "T"]
        else:
            fill = ["T", "S", "T", "S"]

        for i, token in enumerate(fill):
            pattern[12 + i] = token
        return pattern

    def _velocity_for(self, token: str) -> int:
        velocity_table = {
            "K": (72, 80, 92, 104, 116),
            "S": (78, 88, 98, 110, 120),
            "T": (70, 80, 92, 104, 116),
        }
        return velocity_table[token][self._intensity]
