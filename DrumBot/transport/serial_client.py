"""Serial transport wrapper with graceful no-device behavior."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover - depends on local environment
    serial = None  # type: ignore


class SerialClient:
    """Send newline-delimited text lines over a serial port."""

    def __init__(
        self,
        port: str | None,
        baudrate: int,
        enabled: bool = True,
        timeout: float = 0.0,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._enabled = enabled
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
        """Whether a serial device is currently open."""

        return self._serial is not None

    def send_line(self, line: str) -> None:
        """Send one protocol line with trailing newline."""

        if self._serial is None:
            return
        payload = f"{line}\n".encode("utf-8")
        self._serial.write(payload)

    def close(self) -> None:
        """Close serial device if open."""

        if self._serial is None:
            return
        self._serial.close()
        self._serial = None
