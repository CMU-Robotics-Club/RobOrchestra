"""Improvise drums along with whoever is playing the piano.

The design thesis is: predict the grid, don't react to notes. A drum bot
takes real time to swing a stick, so reacting to a note that already sounded
means playing behind it forever. Instead the pianist's note-ons feed a beat
tracker, and once tempo and phase are locked the groove engine writes the
next beat's drum notes onto the *predicted* grid, far enough ahead that
every transport — speakers, old daisy chain, ESP32 bots — can land them on
time. When the tracker is not confident, the drums stay silent: a wrong
groove is worse than none.

The tracker answers when; the Listener answers how. Velocities and pitches
feed it, and once a bar it steers the groove engine: loud piano means hard
drums, a flurry means the drums thin out to leave space, a hole in the
phrase earns a fill, and when the pianist stops the kit fades over about a
bar instead of hammering on alone. Its accent scores also feed the
tracker's downbeat inference, so the backbeat migrates onto 2 and 4 even
when the lock happened mid-bar. Manual controls stay live on top: +/-
becomes a standing offset, a chosen mode pins until "mode auto".

Both real input (MidiInput) and the built-in fake pianist (FakePianoInput)
deliver the same NoteOn type through the same queue, so a demo with no
keyboard exercises the identical pipeline.

Threading: producers (the rtmidi callback or the fake-piano thread) only
enqueue. One tick thread owns the tracker and the groove engine and calls
ensemble.strike_at(); the ensemble takes its own lock, and every timestamp
in the pipeline lives on the ensemble's clock, so the transport, the
tracker and the grid all agree on what "now" means.
"""

from __future__ import annotations

import logging
import queue
import threading
import time

from ..core.beat import BeatTracker
from ..core.ensemble import Ensemble
from ..core.generate import BeatContext, GrooveGenerator, DECORATION, MUTATE, RIFFS
from ..core.groove import GrooveEngine, check_grouping, default_grouping
from ..core.harmony import HarmonyState, HarmonyTracker
from ..core.listen import Feel, Listener
from ..core.meter import best_for_meter, best_guess, score_history
from ..core.phrase import PhraseContext, PhraseTracker
from .base import Control, Source
from .fake_piano import FakePianoInput
from .midi_in import MidiInput, NoteOn

logger = logging.getLogger(__name__)

# Automatic meter detection. The declared meter is the incumbent; a
# challenger has to score well in absolute terms, beat the incumbent's own
# best reading by a clear ratio, and do so on consecutive bar lines before
# the bar changes under the drummer's feet.
METER_WINDOW_BEATS = 36     # whole bars of 3, 4 and 6 alike
METER_MIN_SCORE = 0.8
METER_HYSTERESIS = 1.3
METER_SWITCH_BARS = 3

# Below this the tracker still claims a lock but the evidence is thin;
# scheduling stops here first, so the drums bow out before the lock breaks.
MIN_SCHEDULE_CONFIDENCE = 0.50

# How much earlier than the transports strictly need it each beat is asked
# for. Margin over max_live_lead_s so the beat's first note is never already
# inside the lead window by the time the tick thread hands it over.
EMIT_AHEAD_MARGIN_S = 0.03

TICK_S = 0.005

# Everything the groove engine can ask for. If nobody on stage accepts any
# of these, the jam would be a silent lecture; better to say so up front.
GROOVE_NOTES = (36, 38, 45)

GROOVES = ("generative", "classic")
# Manual +/- steps, as a shift in the generator's activity.
ACTIVITY_PER_STEP = 0.15
SPARSE_ACTIVITY_CAP = 0.25
BUSY_ACTIVITY_FLOOR = 0.8
# The pianist's accent on a beat (from the tracker's bar profile) bends the
# drums' accent on it, within reason.
ACCENT_PULL = 0.3
ACCENT_MIN, ACCENT_MAX = 0.85, 1.25
ACCENT_EVIDENCE = 2.0


def save_session(path: str, events: list[NoteOn]) -> None:
    """One JSON object per line: time, note, velocity. Times start at zero."""
    import json

    origin = events[0].t_s if events else 0.0
    with open(path, "w") as out:
        for ev in events:
            out.write(json.dumps({"t": round(ev.t_s - origin, 4), "note": ev.note,
                                  "velocity": ev.velocity}) + "\n")


def load_session(path: str) -> list[NoteOn]:
    """The inverse of save_session."""
    import json

    events: list[NoteOn] = []
    with open(path) as src:
        for line in src:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            events.append(NoteOn(int(row["note"]), int(row["velocity"]), float(row["t"])))
    return events


def check_stage(instruments: dict) -> list[int]:
    """The groove notes some bot on stage accepts. Raises when there are none."""
    playable = [
        note for note in GROOVE_NOTES
        if any(note in inst.model.accepts for inst in instruments.values())
    ]
    if not playable:
        raise RuntimeError(
            "no bot on stage accepts any groove note "
            f"({', '.join(str(n) for n in GROOVE_NOTES)}); "
            "the jam needs a snare or tom bot"
        )
    return playable


def resource_gaps(instruments: dict) -> tuple[float, float]:
    """Physical floors for the groove engine's pre-thinning, in seconds.

    Kick and tom share a floor only when exactly the same bots accept both,
    which is the ROUTE_BD_TO_TOM reality today; a future dedicated kick bot
    dissolves the coupling here with no code change.
    """
    def accepting(note: int) -> frozenset[str]:
        return frozenset(bot_id for bot_id, inst in instruments.items()
                         if note in inst.model.accepts)

    def floor_s(note: int) -> float:
        gaps = [instruments[b].model.min_gap_ms / 1000.0 for b in accepting(note)]
        return min(gaps) if gaps else 0.0

    kt = max(floor_s(36), floor_s(45)) if accepting(36) == accepting(45) else 0.0
    return kt, floor_s(38)


class JamSource(Source):
    """Piano note-ons in, ensemble.strike_at() out."""

    name = "jam"
    controls = (
        Control("intensity", "int", default=2, lo=0, hi=4,
                help="how busy the groove is"),
        Control("mode", "choice", default="groove",
                choices=("groove", "sparse", "busy")),
        Control("meter", "int", default=4, lo=2, hi=7,
                help="declared beats per bar"),
        Control("min_bpm", "float", default=50.0, lo=30, hi=300),
        Control("max_bpm", "float", default=180.0, lo=40, hi=300),
        Control("preferred_bpm", "float", default=100.0, lo=40, hi=300,
                help="where the beat usually lives; settles octave ambiguity"),
    )

    def __init__(
        self,
        input_port: str | None = None,
        fake_bpm: float | None = None,
        fake_drift_pct_per_min: float = 0.0,
        meter: int = 4,
        min_bpm: float = 50.0,
        max_bpm: float = 180.0,
        intensity: int = 2,
        mode: str = "groove",
        fill_every_bars: int = 8,
        fill_probability: float = 0.30,
        seed: int | None = None,
        follow: bool = True,
        infer_downbeat: bool = True,
        auto_meter: bool = False,
        grouping: tuple[int, ...] | None = None,
        fake_meter: int | None = None,
        preferred_bpm: float = 100.0,
        record_path: str | None = None,
        tempo_hint: float | None = None,
        groove: str = "generative",
        decoration: float = DECORATION,
        riffs: str = "phrase",
        mutation: float = MUTATE,
        min_gap_ms: float | None = None,
        hold: float | None = None,
    ) -> None:
        if groove not in GROOVES:
            raise ValueError(f"unknown groove {groove!r}; one of {', '.join(GROOVES)}")
        self._groove = groove
        if fake_bpm is not None and input_port is not None:
            raise ValueError("pick one pianist: --fake or --input-port, not both")
        if not 0 < min_bpm < max_bpm:
            raise ValueError("need 0 < min_bpm < max_bpm")
        if preferred_bpm <= 0:
            raise ValueError("preferred_bpm must be positive")
        if tempo_hint is not None and tempo_hint <= 0:
            raise ValueError("tempo_hint must be positive")
        self._preferred_bpm = float(preferred_bpm)
        self._tempo_hint = float(tempo_hint) if tempo_hint else None
        # Every note-on, kept so a session can be replayed through the
        # pipeline offline: what the tracker did with real hands is the
        # only evidence that matters, and it should never be lost.
        self._record_path = record_path
        self._recorded: list[NoteOn] = []
        if meter < 1:
            raise ValueError("meter needs at least one beat per bar")
        self._input_port = input_port
        self._fake_bpm = fake_bpm
        self._fake_drift = fake_drift_pct_per_min
        self._fake_meter = int(fake_meter) if fake_meter else None
        self._meter = int(meter)
        self._grouping = tuple(grouping) if grouping else default_grouping(self._meter)
        check_grouping(self._grouping, self._meter)
        self._auto_meter = bool(auto_meter)
        self._meter_candidate: tuple[int, tuple[int, ...]] | None = None
        self._meter_streak = 0
        self._min_bpm = float(min_bpm)
        self._max_bpm = float(max_bpm)
        self._intensity = intensity
        self._mode = mode
        self._fill_every_bars = fill_every_bars
        self._fill_probability = fill_probability
        self._seed = seed
        self._follow = bool(follow)
        self._infer_downbeat = bool(infer_downbeat)
        self._decoration = float(decoration)
        if riffs not in RIFFS:
            raise ValueError(f"riffs must be one of {', '.join(RIFFS)}, not {riffs!r}")
        self._riffs = riffs
        self._mutation = float(mutation)
        if min_gap_ms is not None and min_gap_ms < 0:
            raise ValueError("min_gap_ms cannot be negative")
        self._min_gap_ms = float(min_gap_ms) if min_gap_ms is not None else None
        if hold is not None and not 0.0 <= hold <= 1.0:
            raise ValueError("hold is 0 to 1")
        self._hold = hold

        self._ensemble: Ensemble | None = None
        self._tracker: BeatTracker | None = None
        self._engine: GrooveEngine | None = None
        self._generator: GrooveGenerator | None = None
        self._phrase: PhraseTracker | None = None
        self._harmony: HarmonyTracker | None = None
        self._phrase_ctx: PhraseContext | None = None
        self._harmony_state: HarmonyState | None = None
        self._echo: tuple[int, ...] = ()
        self._activity = 0.5
        self._listener: Listener | None = None
        self._input = None
        self._emit_ahead_s = 0.0
        self._events: queue.SimpleQueue[NoteOn] = queue.SimpleQueue()

        # Manual nudges layered over the automatic following: +/- becomes a
        # standing offset from whatever the listener suggests, and a chosen
        # mode pins it until "mode auto" hands it back.
        self._intensity_bias = 0
        self._last_suggested: int | None = None
        self._mode_override: str | None = None if self._follow else mode
        self._feel: Feel | None = None

        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._running = threading.Event()
        self._error: BaseException | None = None

        # Counters the CLI status line reads. Written by one thread, read by
        # another; ints in CPython make that safe without a lock.
        self.piano_notes = 0
        self.scheduled = 0
        self.stale = 0
        self.gap_fills = 0
        self.meter_switches = 0
        self.input_label = ""

    def bind(self, ensemble: Ensemble) -> None:
        """Wire the pipeline to an ensemble. Split from start() so tests can
        feed _on_note()/_tick() with synthetic events and no input device."""
        check_stage(ensemble.instruments)
        self._ensemble = ensemble
        self._tracker = BeatTracker(
            min_bpm=self._min_bpm,
            max_bpm=self._max_bpm,
            beats_per_bar=self._meter,
            infer_downbeat=self._infer_downbeat,
            preferred_bpm=self._preferred_bpm,
            tempo_hint=self._tempo_hint,
            hold=self._hold,
        )
        kt_gap_s, snare_gap_s = resource_gaps(ensemble.instruments)
        if self._min_gap_ms is not None:
            # A stricter floor than the models claim: what the hardware
            # can do and what it can do well are different numbers.
            kt_gap_s = max(kt_gap_s, self._min_gap_ms / 1000.0)
            snare_gap_s = max(snare_gap_s, self._min_gap_ms / 1000.0)
        self._engine = GrooveEngine(
            intensity=self._intensity,
            mode=self._mode,
            beats_per_bar=self._meter,
            fill_every_bars=self._fill_every_bars,
            fill_probability=self._fill_probability,
            rng_seed=self._seed,
            kt_min_gap_s=kt_gap_s,
            snare_min_gap_s=snare_gap_s,
            grouping=self._grouping,
        )
        self._generator = GrooveGenerator(
            beats_per_bar=self._meter,
            grouping=self._grouping,
            rng_seed=self._seed,
            kt_min_gap_s=kt_gap_s,
            snare_min_gap_s=snare_gap_s,
            decoration=self._decoration,
            riffs=self._riffs,
            mutation=self._mutation,
        )
        self._phrase = PhraseTracker()
        self._harmony = HarmonyTracker()
        self._phrase_ctx = self._phrase.context()
        self._harmony_state = None
        self._echo = ()
        self._listener = Listener(beats_per_bar=self._meter,
                                  keep_time=self._tempo_hint is not None)
        self._lead_floor_s = ensemble.max_live_lead_s()
        self._emit_ahead_s = self._lead_floor_s + EMIT_AHEAD_MARGIN_S

    def _on_note(self, event: NoteOn) -> None:
        """Producer side: any thread may call this; it only enqueues."""
        self.piano_notes += 1
        self._events.put(event)
        if self._record_path is not None:
            self._recorded.append(event)

    def _tick(self, now_s: float) -> None:
        """One pipeline step. The tick thread's whole job, and the test seam."""
        assert self._tracker is not None and self._engine is not None
        assert self._listener is not None
        assert self._ensemble is not None, "bind() before _tick()"

        assert self._generator is not None and self._phrase is not None
        assert self._harmony is not None

        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break
            accent = self._listener.on_note(event.note, event.velocity, event.t_s)
            settled = self._listener.take_settled_credit()
            if settled > 0.0:
                self._tracker.credit_last_cluster(settled)
            self._tracker.on_onset(event.t_s, accent)
            self._harmony.on_note(event.note, event.velocity, event.t_s)

        beats = self._tracker.advance(now_s + self._emit_ahead_s)
        state = self._tracker.state
        period_s = 60.0 / state.bpm if state.bpm else 0.6
        feel = self._listener.feel(now_s, period_s)
        self._feel = feel

        if feel.gap_fill and state.locked and self._riffs != "none":
            # A hole in the phrase earns a fill — but only once there is a
            # bar to put it in. Before the lock a request would just sit
            # there and fire, meaninglessly, in the first bar afterwards.
            self._engine.request_fill()
            self._generator.request_fill()
            self.gap_fills += 1

        if feel.resting or state.confidence < MIN_SCHEDULE_CONFIDENCE:
            return

        for beat in beats:
            index = beat.bar_index * self._meter + (beat.beat_in_bar - 1)
            self._harmony_state = self._harmony.on_beat(index, beat.time_s)
            if beat.beat_in_bar == 1:
                # Bar lines are where a drummer changes texture, where the
                # question of what the bar even is gets asked, and where the
                # bar just finished is weighed for phrase and section.
                if self._auto_meter:
                    self._consider_meter()
                if self._follow:
                    self._last_suggested = feel.intensity
                    self._engine.set_intensity(feel.intensity + self._intensity_bias)
                    self._engine.set_mode(self._mode_override or feel.mode)
                self._phrase_ctx = self._phrase.on_bar(self._listener.bar_features(self._meter))
                self._echo = self._last_bar_rhythm(beat.time_s, beat.period_s)
            if self._groove == "generative":
                notes = self._generator.notes_for_beat(self._beat_context(beat, feel, state))
            else:
                notes = self._engine.notes_for_beat(beat, state.confidence)
            for note in notes:
                if note.time_s < now_s + max(0.0, self._lead_floor_s - 0.010):
                    # The burst of already-unreachable notes right after
                    # locking: behind now, or inside the transport's lead by
                    # more than the ensemble could nudge away.
                    self.stale += 1
                    continue
                velocity = round(note.velocity * feel.velocity_scale)
                if velocity < 1:
                    continue
                result = self._ensemble.strike_at(
                    note.note, velocity, note.time_s, source=self.name)
                if result.ok:
                    self.scheduled += 1

    def _beat_context(self, beat, feel: Feel, state) -> BeatContext:
        """Everything the generator wants to know about this beat."""
        assert self._phrase_ctx is not None and self._harmony is not None
        activity = feel.activity if self._follow else 0.5
        activity += ACTIVITY_PER_STEP * self._intensity_bias
        mode = self._mode_override or (feel.mode if self._follow else self._mode)
        if mode == "sparse":
            activity = min(activity, SPARSE_ACTIVITY_CAP)
        elif mode == "busy":
            activity = max(activity, BUSY_ACTIVITY_FLOOR)
        activity = max(0.05, min(1.0, activity))
        self._activity = activity
        ctx = self._phrase_ctx
        index = beat.bar_index * self._meter + (beat.beat_in_bar - 1)
        return BeatContext(
            time_s=beat.time_s,
            period_s=beat.period_s,
            beat_in_bar=beat.beat_in_bar,
            bar_index=beat.bar_index,
            bar_in_phrase=ctx.bar_in_phrase,
            phrase_end=ctx.phrase_end,
            hyper_end=ctx.hyper_end,
            section_started=ctx.section_started and beat.beat_in_bar == 1,
            activity=activity,
            gain=feel.gain,
            accent=self._accent_for(beat.beat_in_bar),
            swing=state.swing,
            chord_change=self._harmony.expects_change(index),
            echo=self._echo,
        )

    def _accent_for(self, beat_in_bar: int) -> float:
        """How much the pianist leans on this beat, as a factor around 1.0."""
        assert self._tracker is not None
        profile = self._tracker.phase_profile
        if len(profile) < beat_in_bar or sum(profile) < ACCENT_EVIDENCE:
            return 1.0
        mean = sum(profile) / len(profile)
        if mean <= 0.0:
            return 1.0
        factor = 1.0 + ACCENT_PULL * (profile[beat_in_bar - 1] / mean - 1.0)
        return max(ACCENT_MIN, min(ACCENT_MAX, factor))

    def _last_bar_rhythm(self, bar_start_s: float, period_s: float) -> tuple[int, ...]:
        """The pianist's onsets in the bar just finished, as sixteenth positions."""
        assert self._listener is not None
        previous_start = bar_start_s - self._meter * period_s
        sixteenth = period_s / 4.0
        positions = set()
        for t in self._listener.recent_clusters:
            if previous_start - 0.05 <= t < bar_start_s - 0.05:
                pos = round((t - previous_start) / sixteenth)
                if 0 <= pos < 4 * self._meter:
                    positions.add(pos)
        return tuple(sorted(positions))

    def _consider_meter(self) -> None:
        """Once a bar: is the pianist in the meter we think they are?"""
        assert self._tracker is not None and self._engine is not None
        assert self._listener is not None
        guesses = score_history(self._tracker.accent_history(METER_WINDOW_BEATS))
        best = best_guess(guesses)
        if best is None:
            return
        if best.beats_per_bar == self._meter and best.grouping == self._grouping:
            self._meter_candidate, self._meter_streak = None, 0
            return
        incumbent = best_for_meter(guesses, self._meter, self._grouping)
        incumbent_score = incumbent.score if incumbent is not None else 0.0
        if (best.score < METER_MIN_SCORE
                or best.score < METER_HYSTERESIS * max(incumbent_score, 0.25)):
            self._meter_candidate, self._meter_streak = None, 0
            return
        key = (best.beats_per_bar, best.grouping)
        if key == self._meter_candidate:
            self._meter_streak += 1
        else:
            self._meter_candidate, self._meter_streak = key, 1
        if self._meter_streak < METER_SWITCH_BARS:
            return

        self._tracker.set_meter(best.beats_per_bar, best.downbeat_index)
        self._engine.set_meter(best.beats_per_bar, best.grouping)
        self._generator.set_meter(best.beats_per_bar, best.grouping)
        self._listener.set_meter(best.beats_per_bar)
        self._meter = best.beats_per_bar
        self._grouping = best.grouping
        self._meter_candidate, self._meter_streak = None, 0
        self.meter_switches += 1
        logger.info("meter is %d/4 %s from beat index %d",
                    best.beats_per_bar, best.grouping, best.downbeat_index)

    def start(self, ensemble: Ensemble) -> None:
        if self._thread is not None:
            return
        self.bind(ensemble)

        if self._fake_bpm is not None:
            self._input = FakePianoInput(
                bpm=self._fake_bpm,
                beats_per_bar=self._fake_meter or self._meter,
                clock=ensemble.now_s,
                seed=self._seed if self._seed is not None else 0,
                drift_pct_per_min=self._fake_drift,
            )
        else:
            self._input = MidiInput(self._input_port, clock=ensemble.now_s)
        self.input_label = self._input.start(self._on_note)

        self._stop.clear()
        self._running.clear()
        self._error = None
        self._thread = threading.Thread(target=self._run, name="jam-source", daemon=True)
        self._thread.start()
        if not self._running.wait(timeout=5.0):
            self.stop()
            raise RuntimeError("jam pipeline did not start") from self._error

    def _run(self) -> None:
        try:
            self._running.set()
            while not self._stop.is_set():
                self._tick(self._ensemble.now_s())
                time.sleep(TICK_S)
        except BaseException as exc:
            self._error = exc
            logger.exception("jam pipeline stopped")
            self._stop.set()
        finally:
            self._running.set()

    def stop(self) -> None:
        # Input first, so no more events arrive while the tick thread drains.
        if self._input is not None:
            self._input.stop()
            self._input = None
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._record_path is not None and self._recorded:
            save_session(self._record_path, self._recorded)
            self._recorded = []

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    @property
    def error(self) -> BaseException | None:
        return self._error

    @property
    def beat_state(self):
        """Snapshot for the status line. May be a tick stale; never blocks."""
        assert self._tracker is not None, "bind() before beat_state"
        return self._tracker.state

    @property
    def feel(self) -> Feel | None:
        """The listener's latest reading, for the status line."""
        return self._feel

    @property
    def following(self) -> bool:
        return self._follow

    @property
    def meter(self) -> int:
        return self._meter

    @property
    def grouping(self) -> tuple[int, ...]:
        return self._grouping

    @property
    def auto_meter(self) -> bool:
        return self._auto_meter

    @property
    def tempo_hint(self) -> float | None:
        return self._tempo_hint

    @property
    def groove(self) -> str:
        return self._groove

    @property
    def activity(self) -> float:
        return self._activity

    @property
    def phrase_context(self) -> PhraseContext | None:
        return self._phrase_ctx

    @property
    def harmony_state(self) -> HarmonyState | None:
        return self._harmony_state

    @property
    def intensity(self) -> int:
        return self._engine.intensity if self._engine is not None else self._intensity

    @property
    def mode(self) -> str:
        return self._engine.mode if self._engine is not None else self._mode

    def set_intensity(self, value: int) -> None:
        """Set the intensity now. While following, this becomes a standing
        offset from the listener's suggestion, so +/- keeps meaning something
        instead of being overwritten at the next bar line."""
        if self._engine is None:
            return
        value = min(max(int(value), 0), 4)
        if self._follow and self._last_suggested is not None:
            self._intensity_bias = value - self._last_suggested
        else:
            self._intensity_bias = value - 2
        self._engine.set_intensity(value)

    def set_mode(self, value: str) -> None:
        """Pin a mode, or hand it back with "auto" while following."""
        if self._engine is None:
            return
        if str(value).strip().lower() == "auto":
            self._mode_override = None
            return
        self._engine.set_mode(value)    # raises on an unknown mode
        self._mode_override = self._engine.mode

    @property
    def decoration(self) -> float:
        return self._generator.decoration if self._generator else self._decoration

    @property
    def riffs(self) -> str:
        return self._generator.riffs if self._generator else self._riffs

    @property
    def hold(self) -> float | None:
        return self._tracker.hold if self._tracker else self._hold

    def set_decoration(self, value: float) -> None:
        self._decoration = max(0.0, min(1.0, float(value)))
        if self._generator is not None:
            self._generator.set_decoration(self._decoration)

    def set_riffs(self, value: str) -> None:
        if self._generator is not None:
            self._generator.set_riffs(value)      # raises on an unknown value
            self._riffs = self._generator.riffs
        else:
            if value not in RIFFS:
                raise ValueError(f"riffs must be one of {', '.join(RIFFS)}")
            self._riffs = value

    def request_fill(self) -> None:
        if self._engine is not None:
            self._engine.request_fill()
