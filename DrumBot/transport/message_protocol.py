"""Message dataclasses and serialization helpers for robot transport."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandMessage:
    """Command message emitted from a recognized gesture."""

    command: str

    def to_line(self) -> str:
        """Serialize command to newline-delimited protocol line."""

        return f"CMD,{self.command}"


@dataclass(frozen=True)
class HitMessage:
    """Hit message emitted when a strike is detected."""

    zone: str
    velocity: float
    handedness: str
    timestamp_ms: int

    def to_line(self) -> str:
        """Serialize hit to newline-delimited protocol line."""

        velocity_text = f"{min(max(self.velocity, 0.0), 1.0):.2f}"
        return f"HIT,{self.zone},{velocity_text},{self.handedness},{self.timestamp_ms}"
