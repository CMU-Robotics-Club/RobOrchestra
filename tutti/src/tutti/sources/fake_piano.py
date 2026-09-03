"""A pianist made of code, so the jam pipeline runs with nothing plugged in.

The point is not to sound like music — piano events feed the beat tracker,
never the ensemble — but the shape is kept pianistic on purpose: a loud low
root on the downbeat, comped triads rolled a few milliseconds apart, an
occasional off-beat push, gaussian timing jitter, and optional slow tempo
drift. Those are exactly the things a tracker has to survive, so a demo
against this is evidence, not theatre.

bar_events() is a pure function of its inputs, which is what the tests
drive. FakePianoInput wraps it in a thread with the same start()/stop()
surface as MidiInput, so everything downstream of the event queue cannot
tell the difference between this and a real keyboard.
"""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable

from .midi_in import NoteOn

BASS_ROOT = 36      # C2, the bar's lowest and loudest: what downbeat inference feeds on
BASS_FIFTH = 43     # G2
TRIAD = (60, 64, 67)
PUSH_NOTE = 64

PUSH_PROBABILITY = 0.4
MAX_ROLL_S = 0.006      # per-note spread of a rolled chord
MAX_JITTER_S = 0.010


def bar_events(
    bar_index: int,
    bar_start_s: float,
    bpm: float,
    beats_per_bar: int,
    rng: random.Random,
    jitter_ms: float = 6.0,
) -> list[NoteOn]:
    """One bar of comping, timestamps absolute on the caller's clock."""
    period_s = 60.0 / bpm
    sigma_s = (jitter_ms / 1000.0) / 3.0

    def jittered(t: float) -> float:
        return t + max(-MAX_JITTER_S, min(MAX_JITTER_S, rng.gauss(0.0, sigma_s)))

    def vel(mean: int) -> int:
        # Means sit far enough apart that the downbeat stays the loudest.
        return max(1, min(127, round(rng.gauss(mean, 2.0))))

    events: list[NoteOn] = []
    for beat in range(1, beats_per_bar + 1):
        t = bar_start_s + (beat - 1) * period_s
        if beat == 1:
            events.append(NoteOn(BASS_ROOT, vel(100), jittered(t)))
        elif beat == 3 and beats_per_bar >= 4:
            events.append(NoteOn(BASS_FIFTH, vel(84), jittered(t)))
        else:
            roll_s = rng.uniform(0.0, MAX_ROLL_S)
            for i, note in enumerate(TRIAD):
                events.append(NoteOn(note, vel(72), jittered(t + i * roll_s)))

    if beats_per_bar >= 2 and rng.random() < PUSH_PROBABILITY:
        candidates = [b for b in (2, 4) if b <= beats_per_bar]
        push_beat = rng.choice(candidates)
        t = bar_start_s + (push_beat - 0.5) * period_s
        events.append(NoteOn(PUSH_NOTE, vel(58), jittered(t)))

    events.sort(key=lambda e: e.t_s)
    return events


class FakePianoInput:
    """Same start()/stop() surface as MidiInput, no hardware behind it."""

    def __init__(
        self,
        bpm: float = 100.0,
        beats_per_bar: int = 4,
        clock: Callable[[], float] | None = None,
        seed: int | None = 0,
        jitter_ms: float = 6.0,
        drift_pct_per_min: float = 0.0,
        lead_in_s: float = 0.5,
    ) -> None:
        if bpm <= 0:
            raise ValueError("bpm must be positive")
        self._bpm = float(bpm)
        self._beats_per_bar = int(beats_per_bar)
        self._clock = clock if clock is not None else time.monotonic
        self._rng = random.Random(seed)
        self._jitter_ms = float(jitter_ms)
        self._drift_pct_per_min = float(drift_pct_per_min)
        self._lead_in_s = float(lead_in_s)

        self._on_event: Callable[[NoteOn], None] | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, on_event: Callable[[NoteOn], None]) -> str:
        if self._thread is not None:
            return self._label()
        self._on_event = on_event
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="fake-piano", daemon=True)
        self._thread.start()
        return self._label()

    def _label(self) -> str:
        label = f"fake piano at {self._bpm:.0f} BPM, {self._beats_per_bar}/4"
        if self._drift_pct_per_min:
            label += f", drifting {self._drift_pct_per_min:+.1f}%/min"
        return label

    def _run(self) -> None:
        start_s = self._clock() + self._lead_in_s
        bar_start_s = start_s
        bar = 0
        while not self._stop.is_set():
            minutes = (bar_start_s - start_s) / 60.0
            bpm = self._bpm * (1.0 + self._drift_pct_per_min / 100.0 * minutes)
            events = bar_events(bar, bar_start_s, bpm, self._beats_per_bar,
                                self._rng, self._jitter_ms)
            for ev in events:
                while not self._stop.is_set() and self._clock() < ev.t_s:
                    time.sleep(0.002)
                if self._stop.is_set():
                    return
                # Stamped at emission, exactly as a real port's callback would.
                self._on_event(NoteOn(ev.note, ev.velocity, self._clock()))
            bar_start_s += self._beats_per_bar * (60.0 / bpm)
            bar += 1

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
