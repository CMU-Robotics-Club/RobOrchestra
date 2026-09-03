"""What every way of driving the ensemble has in common.

A source is anything that produces musical intent: a score player, a camera
watching hands, a beat tracker listening to a band. Sources never talk to a
transport and never pick a bot; they call ensemble.strike() and the same
physics applies to all of them.

Controls are declared as data rather than argparse calls so that a source
written next semester shows up in the CLI, and later the GUI, without either
of those learning anything about it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..core.ensemble import Ensemble


@dataclass(frozen=True)
class Control:
    """One user-adjustable knob a source declares about itself."""

    name: str
    kind: str                     # "int", "float", "bool", "choice"
    default: object = None
    lo: float | None = None
    hi: float | None = None
    choices: tuple[str, ...] = ()
    help: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ("int", "float", "bool", "choice"):
            raise ValueError(f"unknown control kind {self.kind!r}")
        if self.kind == "choice" and not self.choices:
            raise ValueError(f"choice control {self.name!r} declares no choices")

    def clamp(self, value):
        """Pull a value back inside the declared range."""
        if self.kind == "choice":
            return value if value in self.choices else self.default
        if self.kind == "bool":
            return bool(value)
        value = int(value) if self.kind == "int" else float(value)
        if self.lo is not None:
            value = max(value, type(value)(self.lo))
        if self.hi is not None:
            value = min(value, type(value)(self.hi))
        return value


class Source(ABC):
    """Base for everything that drives the ensemble."""

    name = "source"
    controls: tuple[Control, ...] = ()

    @abstractmethod
    def start(self, ensemble: Ensemble) -> None:
        """Begin producing. Returns once running; work happens on own threads."""

    @abstractmethod
    def stop(self) -> None:
        """Stop producing. Must be safe to call twice."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.stop()
        return False
