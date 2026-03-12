"""Serial and MIDI transport clients with message protocol."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

try:
    import serial  # type: ignore
except Exception:
    serial = None  # type: ignore

try:
    import mido
except Exception:
    mido = None  # type: ignore


# ── Message protocol ─────────────────────────────────────────────────

@dataclass(frozen=True)
class CommandMessage:
    command: str

    def to_line(self) -> str:
        return f"CMD,{self.command}"


@dataclass(frozen=True)
class HitMessage:
    zone: str
    velocity: float
    handedness: str
    timestamp_ms: int

    def to_line(self) -> str:
        v = f"{min(max(self.velocity, 0.0), 1.0):.2f}"
        return f"HIT,{self.zone},{v},{self.handedness},{self.timestamp_ms}"


# ── Serial client ────────────────────────────────────────────────────

class SerialClient:
    def __init__(self, port: str | None, baudrate: int, enabled: bool = True, timeout: float = 0.0) -> None:
        self._serial: Any | None = None

        if not enabled:
            logger.info("Serial transport disabled by config")
            return
        if not port:
            logger.info("Serial port not set; running without transport output")
            return
        if serial is None:
            raise RuntimeError("pyserial is not installed but serial transport is enabled")

        self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        logger.info("Connected serial transport on %s @ %s", port, baudrate)

    @property
    def is_connected(self) -> bool:
        return self._serial is not None

    def send_line(self, line: str) -> None:
        if self._serial is None:
            return
        self._serial.write(f"{line}\n".encode("utf-8"))

    def close(self) -> None:
        if self._serial is None:
            return
        self._serial.close()
        self._serial = None


# ── MIDI client ──────────────────────────────────────────────────────

class MidiClient:
    def __init__(self, enabled: bool, port_name: str | None, channel: int) -> None:
        self._channel = min(max(channel, 0), 15)
        self._ports: list[Any] = []
        self._port_names: list[str] = []

        if not enabled:
            logger.info("MIDI output disabled by config")
            return
        if mido is None:
            raise RuntimeError("mido/python-rtmidi is not installed but MIDI output is enabled")

        available = self.list_output_ports()
        if not available:
            logger.info("No MIDI output ports found")
            return

        selected = self._resolve_output_ports(available, port_name)
        if not selected:
            logger.info("MIDI output enabled but no matching port found")
            return

        for name in selected:
            self._ports.append(mido.open_output(name))
            self._port_names.append(name)
            logger.info("Connected MIDI output: %s (channel=%s)", name, self._channel + 1)

    @property
    def is_connected(self) -> bool:
        return len(self._ports) > 0

    @property
    def connected_output_names(self) -> tuple[str, ...]:
        return tuple(self._port_names)

    @staticmethod
    def list_output_ports() -> list[str]:
        if mido is None:
            return []
        return list(mido.get_output_names())

    def send_note_on(self, note: int, velocity_normalized: float) -> int:
        if not self._ports:
            return 0
        vel = min(max(int(round(velocity_normalized * 127.0)), 1), 127)
        msg = mido.Message("note_on", channel=self._channel, note=min(max(int(note), 0), 127), velocity=vel)
        return self._send(msg)

    def send_note_off(self, note: int) -> int:
        if not self._ports:
            return 0
        msg = mido.Message("note_off", channel=self._channel, note=min(max(int(note), 0), 127), velocity=0)
        return self._send(msg)

    def send_control_change(self, control: int, value: int) -> int:
        if not self._ports:
            return 0
        msg = mido.Message("control_change", channel=self._channel, control=min(max(int(control), 0), 127), value=min(max(int(value), 0), 127))
        return self._send(msg)

    def _send(self, msg: Any) -> int:
        failed_indices: list[int] = []
        delivered = 0
        for idx, port in enumerate(self._ports):
            try:
                port.send(msg)
                delivered += 1
            except Exception:
                logger.warning("MIDI send failed on %s", getattr(port, "name", port), exc_info=True)
                failed_indices.append(idx)
        if failed_indices:
            failed_set = set(failed_indices)
            self._ports = [p for i, p in enumerate(self._ports) if i not in failed_set]
            self._port_names = [n for i, n in enumerate(self._port_names) if i not in failed_set]
        return delivered

    def close(self) -> None:
        for port in self._ports:
            try:
                port.close()
            except Exception:
                pass
        self._ports.clear()
        self._port_names.clear()

    @staticmethod
    def _resolve_output_ports(available: list[str], requested: str | None) -> list[str]:
        if requested:
            if requested in available:
                return [requested]
            lowered = requested.lower()
            matches = [n for n in available if lowered in n.lower()]
            if matches:
                return matches
            logger.warning("Requested MIDI output '%s' was not found", requested)
            logger.info("Available outputs: %s", ", ".join(available))
            return []

        matches = [n for n in available if "roborchestra" in n.lower() or "drumbot" in n.lower()]
        if matches:
            return matches

        logger.info("MIDI outputs available but no default selected; pass --midi-port. Outputs: %s", ", ".join(available))
        return []
