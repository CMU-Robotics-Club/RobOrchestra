"""Conduct the ensemble: a piece, or the old improvised demo, at your tempo.

Beats arrive from wherever they come from — the webcam watching a hand, the
Enter key, a MIDI pad, a built-in metronome for testing — and go into one
ConductorClock, which numbers them and predicts where the next one falls.
A program (ScoreProgram for a piece, Improviser for the old demo) hands out
notes in beat order. This source's tick walks the program as far as the
clock will predict, no further, and schedules each group of notes with
Ensemble.strike_at() early enough for every transport to land it on time.

That "no further" is the whole behaviour. The clock predicts one beat past
the last stroke, so the orchestra plays through the current beat and onto
the next, and if the conductor stops it stops there and waits. The notes on
that next beat are scheduled from the flywheel, because a stick has to be
moving before the baton lands; the notes after it wait for the baton.

Threading follows jam.py: beat producers only enqueue, one tick thread owns
the clock and the program, and every time is on the ensemble's clock.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections.abc import Callable
from pathlib import Path

from ..core.conduct import ConductorClock, Stroke
from ..core.ensemble import Ensemble
from .base import Control, Source

logger = logging.getLogger(__name__)

TICK_S = 0.005
# Margin over the transports' lead, so a beat's first note is never already
# inside the lead window by the time the tick hands it over.
EMIT_AHEAD_MARGIN_S = 0.03
# A note whose moment has passed by less than this is played now; beyond
# it the moment is gone and the note is skipped rather than played late.
LATE_SKIP_S = 0.15
# Once the piece has ended, a stroke after this long a silence starts it
# over: the next count-in plays it again without touching the keyboard.
RESTART_GAP_S = 2.0
# Stroke size to velocity. A conductor's biggest strokes push a little past
# the written dynamics and the smallest pull well under; the floor keeps a
# timid count-in from making the first bar inaudible.
DYNAMICS_FLOOR = 0.45
DYNAMICS_GAIN = 0.85
DYNAMICS_MAX = 1.25


class MetronomeInput:
    """A fake conductor: strokes at a steady tempo, optionally drifting.

    For hearing the whole pipeline with no camera and nobody waving. It is
    also how the tests and the render path get deterministic beats.
    """

    def __init__(self, bpm: float, clock: Callable[[], float],
                 drift_pct_per_min: float = 0.0, strength: float = 0.7) -> None:
        if bpm <= 0:
            raise ValueError("bpm must be positive")
        self._period = 60.0 / bpm
        self._clock = clock
        self._drift = drift_pct_per_min / 100.0 / 60.0    # fraction per second
        self._strength = strength
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self, on_beat: Callable[[float, float], None]) -> str:
        self._on_beat = on_beat
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="metronome", daemon=True)
        self._thread.start()
        return f"metronome at {60.0 / self._period:.0f} BPM"

    def _run(self) -> None:
        next_s = self._clock() + 0.5
        started = self._clock()
        while not self._stop.is_set():
            now = self._clock()
            if now >= next_s:
                self._on_beat(next_s, self._strength)
                elapsed = now - started
                period = self._period / (1.0 + self._drift * elapsed)
                next_s += period
            time.sleep(0.002)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None


class ConductSource(Source):
    """Conductor strokes in, ensemble.strike_at() out."""

    name = "conduct"
    controls = (
        Control("count_in", "int", default=4, lo=2, hi=8,
                help="strokes before the piece begins"),
        Control("dynamics", "bool", default=True,
                help="bigger strokes play louder"),
        Control("coast", "int", default=0, lo=0, hi=4,
                help="beats the orchestra may play past the last stroke"),
    )

    def __init__(
        self,
        program,
        count_in: int = 4,
        camera: bool = True,
        model_path: Path | None = None,
        camera_index: int = 0,
        latency_ms: int = 90,
        detector: str = "predictive",
        mirror: bool = True,
        display: bool = True,
        tap_port: str | None = None,
        fake_bpm: float | None = None,
        fake_drift_pct_per_min: float = 0.0,
        dynamics: bool = True,
        coast: int = 0,
        min_bpm: float = 30.0,
        max_bpm: float = 240.0,
    ) -> None:
        if not 0 < min_bpm < max_bpm:
            raise ValueError("need 0 < min_bpm < max_bpm")
        self._program = program
        self._count_in = int(count_in)
        self._camera = bool(camera)
        self._model_path = model_path
        self._camera_index = camera_index
        self._latency_ms = latency_ms
        self._detector = detector
        self._mirror = mirror
        self._display = display
        self._tap_port = tap_port
        self._fake_bpm = fake_bpm
        self._fake_drift = fake_drift_pct_per_min
        self._dynamics = bool(dynamics)
        self._coast = int(coast)
        self._min_period_s = 60.0 / max_bpm
        self._max_period_s = 60.0 / min_bpm

        self._ensemble: Ensemble | None = None
        self._clock: ConductorClock | None = None
        self._strokes: queue.SimpleQueue[tuple[float, float]] = queue.SimpleQueue()
        self._baton = None
        self._midi = None
        self._metronome = None
        self._lead_floor_s = 0.0
        self._emit_ahead_s = 0.0

        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._running = threading.Event()
        self._error: BaseException | None = None

        # Counters the CLI status line reads. Written by one thread, read by
        # another; ints in CPython make that safe without a lock.
        self.scheduled = 0
        self.skipped = 0
        self.restarts = 0
        self.input_labels: list[str] = []
        self._last_stroke: Stroke | None = None

    def bind(self, ensemble: Ensemble) -> None:
        """Wire the pipeline to an ensemble. Split from start() so tests can
        feed on_stroke()/_tick() with synthetic beats and no camera."""
        self._ensemble = ensemble
        self._clock = ConductorClock(
            count_in=self._count_in,
            min_period_s=self._min_period_s,
            max_period_s=self._max_period_s,
            coast_beats=self._coast,
        )
        self._lead_floor_s = ensemble.max_live_lead_s()
        self._emit_ahead_s = self._lead_floor_s + EMIT_AHEAD_MARGIN_S

    # beats in

    def on_stroke(self, t_s: float, strength: float = 1.0) -> None:
        """Any thread may call this; it only enqueues."""
        self._strokes.put((float(t_s), float(strength)))

    def tap(self, strength: float = 1.0) -> None:
        """A beat right now, from a key or a button."""
        assert self._ensemble is not None, "bind() before tap()"
        self.on_stroke(self._ensemble.now_s(), strength)

    def restart(self) -> None:
        """Back to the top: the next strokes are a fresh count-in."""
        self._strokes.put((float("nan"), 0.0))

    # the tick

    def _tick(self, now_s: float) -> None:
        """One pipeline step. The tick thread's whole job, and the test seam."""
        assert self._clock is not None and self._ensemble is not None, "bind() before _tick()"
        clock, program = self._clock, self._program

        while True:
            try:
                t, strength = self._strokes.get_nowait()
            except queue.Empty:
                break
            if t != t:      # NaN: an explicit restart
                self._restart()
                continue
            last = clock.last_stroke_s
            if program.finished and last is not None and t - last > RESTART_GAP_S:
                self._restart()
            stroke = clock.on_stroke(t, strength)
            self._last_stroke = stroke
            if stroke.kind == "restart":
                program.reset()

        if not clock.started:
            return

        horizon = now_s + self._emit_ahead_s
        scale = self._velocity_scale()
        while True:
            beat = program.next_beat()
            if beat is None:
                break
            at = clock.time_of_beat(beat)
            if at is None or at > horizon:
                break       # the conductor has not reached this beat yet
            notes = program.pop_next()
            if at < now_s + self._lead_floor_s - 0.010:
                if now_s - at > LATE_SKIP_S:
                    # The conductor jumped ahead: this moment is gone.
                    self.skipped += len(notes)
                    continue
                at = now_s + self._lead_floor_s + 0.002
            for note in notes:
                velocity = max(1, min(127, round(note.velocity * scale)))
                result = self._ensemble.strike_at(note.note, velocity, at, source=self.name)
                if result.ok:
                    self.scheduled += 1

    def _restart(self) -> None:
        assert self._clock is not None
        self._clock.reset()
        self._program.reset()
        self.restarts += 1

    def _velocity_scale(self) -> float:
        if not self._dynamics or self._clock is None:
            return 1.0
        return min(DYNAMICS_MAX, DYNAMICS_FLOOR + DYNAMICS_GAIN * self._clock.dynamics)

    # lifecycle

    def start(self, ensemble: Ensemble) -> None:
        if self._thread is not None:
            return
        self.bind(ensemble)
        self.input_labels = []

        if self._fake_bpm is not None:
            self._metronome = MetronomeInput(
                self._fake_bpm, clock=ensemble.now_s, drift_pct_per_min=self._fake_drift)
            self.input_labels.append(self._metronome.start(self.on_stroke))
        if self._tap_port is not None:
            from .midi_in import MidiInput
            self._midi = MidiInput(self._tap_port, clock=ensemble.now_s)
            name = self._midi.start(
                lambda ev: self.on_stroke(ev.t_s, ev.velocity / 127.0))
            self.input_labels.append(f"MIDI taps on {name}")
        if self._camera:
            from .baton import BatonSource
            self._baton = BatonSource(
                on_beat=self.on_stroke,
                model_path=self._model_path,
                camera_index=self._camera_index,
                latency_ms=self._latency_ms,
                detector=self._detector,
                mirror=self._mirror,
                display=self._display,
            )
            self._baton.start(ensemble)
            self.input_labels.append("the webcam")
        self.input_labels.append("Enter")

        self._stop.clear()
        self._running.clear()
        self._error = None
        self._thread = threading.Thread(target=self._run, name="conduct-source", daemon=True)
        self._thread.start()
        if not self._running.wait(timeout=5.0):
            self.stop()
            raise RuntimeError("conduct pipeline did not start") from self._error

    def _run(self) -> None:
        next_overlay = 0.0
        try:
            self._running.set()
            while not self._stop.is_set():
                now = self._ensemble.now_s()
                self._tick(now)
                if self._baton is not None and now >= next_overlay:
                    next_overlay = now + 0.1
                    self._baton.status_text = self.overlay_text(now)
                if self._baton is not None and self._baton.stopped:
                    self._error = self._baton.error
                    break
                time.sleep(TICK_S)
        except BaseException as exc:
            self._error = exc
            logger.exception("conduct pipeline stopped")
        finally:
            self._stop.set()
            self._running.set()

    def stop(self) -> None:
        for producer in (self._metronome, self._midi, self._baton):
            if producer is not None:
                producer.stop()
        self._metronome = self._midi = self._baton = None
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    # for the CLI

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    @property
    def error(self) -> BaseException | None:
        return self._error

    @property
    def program(self):
        return self._program

    @property
    def clock(self) -> ConductorClock | None:
        return self._clock

    @property
    def last_stroke(self) -> Stroke | None:
        return self._last_stroke

    @property
    def frames(self) -> int:
        return self._baton.frames if self._baton is not None else 0

    @property
    def latency_ms_mean(self) -> float:
        return self._baton.latency_ms_mean if self._baton is not None else 0.0

    def poll_display(self):
        """The newest preview frame, or None. Only when a camera is running."""
        return self._baton.poll_display() if self._baton is not None else None

    def overlay_text(self, now_s: float) -> str:
        """One line for the preview window: tempo, where we are, and holds."""
        clock = self._clock
        if clock is None or not clock.started:
            n = clock.strokes if clock is not None else 0
            return f"count in: {n}/{self._count_in}"
        text = f"{clock.bpm:.0f} BPM  {self._program.describe()}"
        if clock.anchor_beat < 0:
            text += f"  count in {clock.strokes}/{self._count_in}"
        if clock.holding(now_s):
            text += "  HOLD"
        return text
