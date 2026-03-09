"""Per-hand temporal state used by hit detection."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class MotionSample:
    """Single hand position observation in normalized image coordinates."""

    timestamp_ms: int
    x: float
    y: float


@dataclass
class HandState:
    """Rolling state for one tracked hand."""

    hand_id: int
    handedness: str
    history_size: int
    samples: deque[MotionSample] = field(init=False)
    last_velocity: float = 0.0
    last_hit_timestamp_ms: int = -1
    last_seen_timestamp_ms: int = -1

    def __post_init__(self) -> None:
        self.samples = deque(maxlen=self.history_size)

    def add_sample(self, sample: MotionSample) -> None:
        """Append a sample and refresh last seen timestamp."""

        self.samples.append(sample)
        self.last_seen_timestamp_ms = sample.timestamp_ms


class HandStateStore:
    """Container for active hand states."""

    def __init__(self, history_size: int) -> None:
        self._history_size = history_size
        self._states: dict[int, HandState] = {}

    def get_or_create(self, hand_id: int, handedness: str) -> HandState:
        """Get existing state or initialize a new one."""

        state = self._states.get(hand_id)
        if state is None:
            state = HandState(
                hand_id=hand_id,
                handedness=handedness,
                history_size=self._history_size,
            )
            self._states[hand_id] = state
        else:
            state.handedness = handedness
        return state

    def prune_stale(self, current_timestamp_ms: int, stale_after_ms: int = 1500) -> None:
        """Drop states that have not been seen recently."""

        stale_ids = [
            hand_id
            for hand_id, state in self._states.items()
            if state.last_seen_timestamp_ms >= 0
            and current_timestamp_ms - state.last_seen_timestamp_ms > stale_after_ms
        ]
        for hand_id in stale_ids:
            del self._states[hand_id]
