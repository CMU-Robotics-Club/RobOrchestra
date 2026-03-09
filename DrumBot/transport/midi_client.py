"""MIDI output wrapper for desktop BLE-MIDI routing via CoreMIDI/rtmidi."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import mido
except Exception:  # pragma: no cover - depends on local environment
    mido = None  # type: ignore


class MidiClient:
    """Send note/control MIDI messages to an output port."""

    def __init__(
        self,
        enabled: bool,
        port_name: str | None,
        channel: int,
    ) -> None:
        self._enabled = enabled
        self._port_name = port_name
        self._channel = min(max(channel, 0), 15)
        self._port: Any | None = None

        if not enabled:
            logger.info("MIDI output disabled by config")
            return

        if mido is None:
            raise RuntimeError("mido/python-rtmidi is not installed but MIDI output is enabled")

        available = self.list_output_ports()
        if not available:
            logger.info("No MIDI output ports found")
            return

        selected_port = self._resolve_output_port(available, port_name)
        if selected_port is None:
            logger.info("MIDI output enabled but no matching port found")
            return

        self._port = mido.open_output(selected_port)
        logger.info("Connected MIDI output: %s (channel=%s)", selected_port, self._channel + 1)

    @property
    def is_connected(self) -> bool:
        """Whether an output port is currently open."""

        return self._port is not None

    @staticmethod
    def list_output_ports() -> list[str]:
        """Return available system MIDI output port names."""

        if mido is None:
            return []
        return list(mido.get_output_names())

    def send_note_on(self, note: int, velocity_normalized: float) -> None:
        """Send note-on with velocity scaled from [0.0, 1.0] to [1, 127]."""

        if self._port is None:
            return

        clamped_note = min(max(int(note), 0), 127)
        velocity = min(max(int(round(velocity_normalized * 127.0)), 1), 127)
        msg = mido.Message(
            "note_on",
            channel=self._channel,
            note=clamped_note,
            velocity=velocity,
        )
        self._port.send(msg)

    def send_control_change(self, control: int, value: int) -> None:
        """Send MIDI control change for gesture command events."""

        if self._port is None:
            return

        cc = min(max(int(control), 0), 127)
        cc_value = min(max(int(value), 0), 127)
        msg = mido.Message(
            "control_change",
            channel=self._channel,
            control=cc,
            value=cc_value,
        )
        self._port.send(msg)

    def close(self) -> None:
        """Close output port if connected."""

        if self._port is None:
            return
        self._port.close()
        self._port = None

    def _resolve_output_port(self, available: list[str], requested: str | None) -> str | None:
        """Resolve explicit or implicit port selection."""

        if requested:
            lowered = requested.lower()
            exact = next((name for name in available if name == requested), None)
            if exact is not None:
                return exact
            contains = next((name for name in available if lowered in name.lower()), None)
            if contains is not None:
                return contains
            logger.warning("Requested MIDI output '%s' was not found", requested)
            logger.info("Available outputs: %s", ", ".join(available))
            return None

        # Auto-pick likely BLE target name when user does not provide one.
        preferred = next(
            (
                name
                for name in available
                if "roborchestra" in name.lower() or "drumbot" in name.lower()
            ),
            None,
        )
        if preferred is not None:
            return preferred

        logger.info(
            "MIDI outputs available but no default selected; pass --midi-port. Outputs: %s",
            ", ".join(available),
        )
        return None
