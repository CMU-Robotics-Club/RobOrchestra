"""Hand tracking, hit detection, zone mapping, and gesture routing."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Mapping, Sequence


# ── Hand state ───────────────────────────────────────────────────────

@dataclass
class MotionSample:
    timestamp_ms: int
    x: float
    y: float


@dataclass
class HandState:
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
        self.samples.append(sample)
        self.last_seen_timestamp_ms = sample.timestamp_ms


class HandStateStore:
    def __init__(self, history_size: int) -> None:
        self._history_size = history_size
        self._states: dict[int, HandState] = {}

    def get_or_create(self, hand_id: int, handedness: str) -> HandState:
        state = self._states.get(hand_id)
        if state is None:
            state = HandState(hand_id=hand_id, handedness=handedness, history_size=self._history_size)
            self._states[hand_id] = state
        else:
            state.handedness = handedness
        return state

    def prune_stale(self, current_timestamp_ms: int, stale_after_ms: int = 1500) -> None:
        stale_ids = [
            hid for hid, s in self._states.items()
            if s.last_seen_timestamp_ms >= 0
            and current_timestamp_ms - s.last_seen_timestamp_ms > stale_after_ms
        ]
        for hid in stale_ids:
            del self._states[hid]


# ── Hit detection ────────────────────────────────────────────────────

@dataclass(frozen=True)
class HitEvent:
    hand_id: int
    handedness: str
    x: float
    y: float
    velocity: float
    timestamp_ms: int


class HitDetector:
    _STRIKE_LANDMARK_INDEX = 9

    def __init__(self, min_travel: float, velocity_threshold: float, cooldown_ms: int, velocity_cap: float) -> None:
        self._min_travel = min_travel
        self._velocity_threshold = velocity_threshold
        self._cooldown_ms = cooldown_ms
        self._velocity_cap = velocity_cap

    def update(self, hand_state: HandState, landmarks: Sequence[tuple[float, float, float]], timestamp_ms: int) -> HitEvent | None:
        if not landmarks:
            return None

        x, y = self._strike_point(landmarks)
        current = MotionSample(timestamp_ms=timestamp_ms, x=x, y=y)
        hand_state.add_sample(current)

        if len(hand_state.samples) < 2:
            return None

        prev = hand_state.samples[-2]
        dt = (current.timestamp_ms - prev.timestamp_ms) / 1000.0
        if dt <= 0:
            return None

        prior_vel = hand_state.last_velocity
        cur_vel = (current.y - prev.y) / dt
        hand_state.last_velocity = cur_vel

        if not (prior_vel < self._velocity_threshold <= cur_vel):
            return None
        y_vals = [s.y for s in hand_state.samples]
        if (max(y_vals) - min(y_vals)) < self._min_travel:
            return None
        if hand_state.last_hit_timestamp_ms >= 0 and (timestamp_ms - hand_state.last_hit_timestamp_ms) < self._cooldown_ms:
            return None

        hand_state.last_hit_timestamp_ms = timestamp_ms
        return HitEvent(
            hand_id=hand_state.hand_id, handedness=hand_state.handedness,
            x=x, y=y,
            velocity=min(max(cur_vel / self._velocity_cap, 0.0), 1.0),
            timestamp_ms=timestamp_ms,
        )

    def _strike_point(self, landmarks: Sequence[tuple[float, float, float]]) -> tuple[float, float]:
        idx = self._STRIKE_LANDMARK_INDEX if len(landmarks) > self._STRIKE_LANDMARK_INDEX else 0
        x, y, _ = landmarks[idx]
        return x, y


# ── Zone mapping ─────────────────────────────────────────────────────

class ZoneMapper:
    def __init__(self, zone_edges: Sequence[float], zone_labels: Sequence[str] = ("SNARE", "TOM")) -> None:
        if len(zone_labels) != len(zone_edges) + 1:
            raise ValueError("zone_labels must contain exactly len(zone_edges) + 1 items")
        if any(e <= 0.0 or e >= 1.0 for e in zone_edges):
            raise ValueError("zone_edges must be within (0, 1)")
        if any(a >= b for a, b in zip(zone_edges, zone_edges[1:])):
            raise ValueError("zone_edges must be strictly increasing")
        self._zone_edges = tuple(zone_edges)
        self._zone_labels = tuple(zone_labels)

    def zone_for_x(self, x: float) -> str:
        clamped = min(max(x, 0.0), 1.0)
        for i, edge in enumerate(self._zone_edges):
            if clamped < edge:
                return self._zone_labels[i]
        return self._zone_labels[-1]


# ── Gesture routing ──────────────────────────────────────────────────

@dataclass(frozen=True)
class CommandEvent:
    command: str
    label: str
    handedness: str
    timestamp_ms: int


class GestureRouter:
    def __init__(self, label_to_command: Mapping[str, str], cooldown_ms: int = 900) -> None:
        self._label_to_command = dict(label_to_command)
        self._cooldown_ms = cooldown_ms
        self._last_emitted_ms: dict[tuple[str, str], int] = {}

    def route(self, label: str | None, handedness: str, timestamp_ms: int) -> CommandEvent | None:
        if not label:
            return None
        command = self._label_to_command.get(label)
        if command is None:
            return None
        key = (command, handedness)
        prior = self._last_emitted_ms.get(key)
        if prior is not None and (timestamp_ms - prior) < self._cooldown_ms:
            return None
        self._last_emitted_ms[key] = timestamp_ms
        return CommandEvent(command=command, label=label, handedness=handedness, timestamp_ms=timestamp_ms)
