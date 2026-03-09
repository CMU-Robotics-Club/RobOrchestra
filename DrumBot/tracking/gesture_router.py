"""Routes MediaPipe gesture labels into robot command events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CommandEvent:
    """A command generated from a recognized gesture label."""

    command: str
    label: str
    handedness: str
    timestamp_ms: int


class GestureRouter:
    """Maps gesture labels to commands and rate-limits repeats."""

    def __init__(self, label_to_command: Mapping[str, str], cooldown_ms: int = 900) -> None:
        self._label_to_command = dict(label_to_command)
        self._cooldown_ms = cooldown_ms
        self._last_emitted_ms: dict[tuple[str, str], int] = {}

    def route(self, label: str | None, handedness: str, timestamp_ms: int) -> CommandEvent | None:
        """Translate one gesture label into a command event, if any."""

        if not label:
            return None

        command = self._label_to_command.get(label)
        if command is None:
            return None

        key = (command, handedness)
        prior_emit = self._last_emitted_ms.get(key)
        if prior_emit is not None and (timestamp_ms - prior_emit) < self._cooldown_ms:
            return None

        self._last_emitted_ms[key] = timestamp_ms
        return CommandEvent(
            command=command,
            label=label,
            handedness=handedness,
            timestamp_ms=timestamp_ms,
        )
