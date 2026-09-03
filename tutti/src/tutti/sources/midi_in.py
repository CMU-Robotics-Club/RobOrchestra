"""One MIDI input port, wrapped so the rest of tutti never touches mido.

Two jobs. Port resolution follows the same convention as the output side in
legacy_din: exact name, then case-insensitive substring, then known hints,
never an index — an index changes with the laptop and the order things were
plugged in, and a rehearsal should not start twenty minutes late over it.

The second job is shutdown. mido's input port close() can block forever on
macOS once the port has taken traffic (recorded in .notes/PLAN.md). What
actually matters when stopping is that no more events reach the pipeline,
and that is a flag flip; the close itself is handed to a daemon thread the
interpreter is free to abandon, so stop() returns promptly no matter what
CoreMIDI is doing.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass

# How a Yamaha P-45 announces itself on macOS is "Digital Piano"; the rest
# cover the common ways a keyboard's port tends to be named.
INPUT_HINTS = ("digital piano", "p-45", "piano", "keyboard", "usb-midi", "usb midi")


@dataclass(frozen=True)
class NoteOn:
    """One key press. Velocity-0 note-ons are note-offs and never arrive here."""

    note: int
    velocity: int   # 1..127
    t_s: float      # arrival time on the clock the owner supplied


class MidiInput:
    """A callback-driven MIDI input with a stop() that cannot hang."""

    def __init__(self, port_name: str | None, clock: Callable[[], float]) -> None:
        self._requested = port_name
        self._clock = clock
        self._on_event: Callable[[NoteOn], None] | None = None
        self._port = None
        self._closed = False

    @staticmethod
    def list_inputs() -> list[str]:
        try:
            import mido
        except Exception:
            return []
        return list(mido.get_input_names())

    @staticmethod
    def resolve_port(available: list[str], requested: str | None) -> str | None:
        """Match a port by exact name, then by substring, case insensitively."""
        if not available:
            return None
        if requested:
            if requested in available:
                return requested
            lowered = requested.lower()
            for name in available:
                if lowered in name.lower():
                    return name
            return None
        for hint in INPUT_HINTS:
            for name in available:
                if hint in name.lower():
                    return name
        return available[0]

    def start(self, on_event: Callable[[NoteOn], None]) -> str:
        """Open the port and begin delivering NoteOns. Returns the port name."""
        import mido

        available = self.list_inputs()
        name = self.resolve_port(available, self._requested)
        if name is None:
            raise RuntimeError(
                f"no MIDI input matched {self._requested!r}. "
                f"Available: {', '.join(available) or 'none'}"
            )
        self._on_event = on_event
        self._closed = False
        # Callback delivery: rtmidi invokes it on its own thread within about
        # a millisecond, and there is nothing to poll or join.
        self._port = mido.open_input(name, callback=self._on_msg)
        return name

    def _on_msg(self, msg) -> None:
        # rtmidi's thread; keep it tiny and never raise out of it.
        if self._closed or self._on_event is None:
            return
        if msg.type == "note_on" and msg.velocity > 0:
            self._on_event(NoteOn(note=msg.note, velocity=msg.velocity,
                                  t_s=self._clock()))

    def stop(self) -> None:
        """Stop delivering events immediately. Never blocks; safe to call twice."""
        self._closed = True
        port, self._port = self._port, None
        if port is None:
            return
        closer = threading.Thread(target=port.close, name="midi-in-close", daemon=True)
        closer.start()
        closer.join(timeout=0.5)
        # If close() hung, the daemon thread is abandoned and the process can
        # still exit; the flag above already made the callback a no-op.
