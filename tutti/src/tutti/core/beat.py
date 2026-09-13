"""Find the pulse in a stream of note onsets, and predict where it lands next.

A reactive accompanist is always late: by the time a note is heard, the moment
to play with it has passed, and a robot adds its own mechanical travel on top.
So the question this tracker answers is not "was that a beat?" but "when is
the next one?" — lock onto the pulse, keep a flywheel spinning through
syncopation and short silences, and let onsets nudge the phase rather than
command it.

Three ideas carry it:

- Tempo comes from tempo.py, which scores candidate periods against the
  whole recent onset pattern rather than voting on adjacent gaps, so swing
  and octave ambiguity are decided on evidence. The runners-up stay alive
  as hypotheses, and the tracker changes its mind only when one of them
  beats the incumbent clearly on several onsets running — a burst of
  syncopation does not retune the band.
- Phase is a flywheel. On-grid onsets pull the predicted grid a little;
  off-grid ones (a push on the "and") are ignored, because following them
  would shift the beat count; only a run of them means the grid itself is
  wrong, and only then does it re-acquire.
- Rubato is read separately from tempo: the last few on-grid onsets give a
  local period, and when it differs from the global one for real the beats
  stretch or shrink with it, so a ritardando at a phrase end is followed
  rather than steamrolled, while the tempo hypotheses stay unbothered.

Onsets closer together than min_onset_gap_s merge into one — a chord is
one event — and their accents (from the Listener) weigh both the tempo
evidence and the per-bar downbeat inference. Confidence decay is per second,
not per update call, so the tick rate of the caller does not change how fast
the tracker gives up.

Not thread-safe by design: one thread drives on_onset() and advance(), the
same posture BotState takes.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import ceil, log, sqrt

from .tempo import TOP_HYPOTHESES, TempoHypothesis, rank_periods, same_period

LOCK_CONFIDENCE = 0.55
UNLOCK_CONFIDENCE = 0.40
MIN_ONSETS_TO_LOCK = 5

# A declared tempo. The player has said where the beat is, so the tracker
# does not have to discover it: the prior narrows to a band around the
# hint, a candidate inside that band locks on less evidence and sooner, a
# challenger outside it needs a clearer win, and the flywheel keeps time
# through a rest for a couple of bars rather than giving up in seconds —
# which is what a drummer who knows the song does.
HINT_PRIOR_WIDTH = 0.25         # octaves, symmetric: about ±19% at one sigma
HINT_BAND = 0.12                # a candidate this close to the hint is "the tempo"
HINT_LOCK_CONFIDENCE = 0.45
HINT_LOCK_REGULARITY = 0.5
HINT_LOCK_STREAK = 2
HINT_MIN_ONSETS = 4
HINT_CHALLENGER_DOMINANCE = 1.6     # for a challenger outside the band
# Through a rest the Listener's fade owns the dropout (it starts about two
# bars in and takes a bar); the tracker only lets go after that would be
# over, so the kit fades out rather than being cut off.
HINT_SILENCE_GRACE_BEATS = 11.0
HINT_SILENCE_UNLOCK_BEATS = 12.0
# The count-in. Two consecutive gaps at the declared tempo — or at half,
# double, or a few multiples of it — and the drummer is in, the way a band
# comes in on "one, two, three, four". No ranking needed.
COUNT_IN_GAPS = 2
COUNT_IN_TOLERANCE = 0.08
COUNT_IN_EVIDENCE = 0.8
# A hint is a prior, not a cage. When the playing supports some other
# period overwhelmingly and the period near the hint only poorly — a 3:2
# misfit, say, because the hint was simply wrong for the piece — the
# evidence wins, and the drums play what the pianist is actually playing.
HINT_OVERRIDE_SUPPORT = 0.6         # the evidence must be this strong
HINT_OVERRIDE_RATIO = 0.75          # and the near-hint reading this much weaker
# ...and the evidence must be for a period *unrelated* to the hint. Double,
# half, triple and their kin are what a hint exists to settle; only a
# period the hint cannot explain at all — a 4:3 misfit — overrules it.
HINT_RELATED = (0.25, 1.0 / 3.0, 0.5, 2.0 / 3.0, 1.0, 1.5, 2.0, 3.0, 4.0)
HINT_RELATED_TOLERANCE = 0.06
# A handful of random onsets always fits *some* period for a moment, since
# the candidates are read off the onsets themselves. So the first lock, like
# every later change of mind, needs the same hypothesis to top the ranking
# on consecutive onsets, and the evidence is discounted while the window is
# thin: with fewer than FULL_EVIDENCE_ONSETS in it, a perfect score is not
# yet a perfect score.
LOCK_STREAK = 6
LOCK_STREAK_STRONG = 3          # a clean pulse need not wait as long
STRONG_SUPPORT = 0.85
# Between the two the wait grades smoothly with support. A hard line at
# STRONG_SUPPORT made the lock time a coin flip for a pulse sitting near
# it — an accelerando from the first bar reads 0.83 or 0.86 depending on
# how the chords happened to be weighted, and waited three onsets or six.
FULL_EVIDENCE_ONSETS = 6
# The candidate's refined period wobbles a few percent as the window
# slides; the candidate follows it rather than being reset by it.
LOCK_CANDIDATE_TOLERANCE = 0.08
# When the ranking is close, the lock goes to the best-supported reading
# among the near-top scores, not the top score itself. An even stream of
# fast notes scores a triplet grouping and a binary one within a whisker of
# each other on the prior; the binary one is the one the onsets actually
# sit on, and the one a drummer would pick.
NEAR_TOP_SCORE = 0.85

# Regularity: the share of recent gaps between onsets that are either a
# simple multiple or subdivision of the period, or a repeat of a gap one or
# two back — a rhythmic cell. Periodicity scoring searches many candidates
# and credits subdivisions, which is exactly what a run of free playing can
# borrow for a moment; adjacent gaps cannot be borrowed. Every real rhythm
# passes — a push is ½, a chord every two beats is 2, and swing at any
# ratio is long-short-long-short, each gap the twin of the one two back —
# and random gaps almost never do.
REGULARITY_IOIS = 8
REGULARITY_MULTIPLES = (0.25, 1.0 / 3.0, 0.5, 2.0 / 3.0, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)
REGULARITY_TOLERANCE_LOCK = 0.05    # to earn the lock: tight
REGULARITY_TOLERANCE_HOLD = 0.08    # to keep it through a bending tempo: looser
REGULARITY_FLOOR_S = 0.02           # hands jitter about this much whatever the gap
SUBDIVISION_REGULARITY = 0.5        # a lone subdivision gap is half the evidence
LOCK_REGULARITY = 0.6
# A run — a scale, an arpeggio, a stream of even notes — puts most of its
# onsets on subdivisions of any beat, so no beat-level reading can score
# high on-grid support, however even the run is. But an even run *is* a
# pulse, and a drummer takes it. Near-perfect regularity therefore earns
# the lock at a lower support line.
RUN_REGULARITY = 0.85
RUN_SUPPORT = 0.40

# Multi-hypothesis tempo. A challenger must top the ranking on this many
# consecutive onsets and beat the incumbent's own current score by this
# ratio before it takes over. The tempo estimate itself follows the active
# hypothesis with inertia once locked, and more eagerly before.
CHALLENGER_STREAK = 3
CHALLENGER_DOMINANCE = 1.25
TEMPO_ALPHA_LOCKED = 0.15
TEMPO_ALPHA_FREE = 0.35
# No challenger is entertained while the grid is landing on the onsets. A
# tempo that fits is right by definition for the drummer; the window's
# periodicity disagreeing with it means the window is stale — a ritardando
# has bent the tempo away from the six seconds behind it — not that the
# tempo is wrong. When the pianist really jumps tempo the grid stops
# fitting, and then the challengers get their hearing.
CHALLENGER_FIT_CEILING = 0.75
# Half-time and the beat explain the same onsets, and the prior chose
# between them at lock. It does not get to choose again every time the
# window slides: mid-piece, octave-equivalent readings with comparable
# support — support, not score, because the prior is exactly what must
# not vote here — are settled by continuity with the tempo being followed.
# The ratio tolerance is loose because through an accelerando the window
# straddles two tempi and every reading in it is smeared.
OCTAVE_RATIOS = (0.25, 1.0 / 3.0, 0.5, 2.0, 3.0, 4.0)
OCTAVE_TOLERANCE = 0.12
OCTAVE_EQUIVALENCE = 0.8        # support ratio for "explains the onsets as well"

# How hard one onset may pull the predicted grid. 0.30 is the flywheel's
# stiffness: high enough to track drift, low enough that a syncopated hit
# does not yank the beat onto itself. An onset further off the grid than
# the window is syncopation and says nothing about phase at all — a push on
# the "and" sits half a period out, and following it would shift the whole
# beat count by one. Only a run of such onsets means the grid itself is
# wrong (locked onto the offbeats), and only then does it re-acquire.
PHASE_NUDGE = 0.30
PHASE_NUDGE_RUBATO = 0.70       # under expressive timing, follow more, fly less
PHASE_NUDGE_WINDOW = 0.30
OFFGRID_RESET_STREAK = 3
# Hold: how firmly the grid is a flywheel rather than a follower, 0 to 1.
# Under hold the phase yields less to each onset and to fewer of them, a
# wrong note between beats is not read as evidence against the grid, it
# takes a longer run of off-grid onsets to move the bar, and rubato bends
# less before the tempo itself follows. Off by default: stray notes are
# already ignored by the flywheel (measured: 23 ms grid error against 19
# at full hold), and a stiffer grid fits an expressive pianist worse. It
# is there for a player who wants the beat to stay put through pushes.
HOLD_NUDGE = 0.7                # fraction of the nudge hold takes away, at 1
HOLD_WINDOW = 0.4
HOLD_STREAK = 4                 # extra off-grid onsets needed before re-acquiring
HOLD_RUBATO = 0.6
HOLD_OFFGRID_FIT = 0.5          # what a stray onset scores against the grid, at 1

# How an onset reads against the grid, for the grid-fit confidence. Tight
# is a hit and is the only thing rubato is read from; sloppy still nudges
# the grid but is thin evidence that the grid is right; a subdivision — an
# eighth, a swung eighth, a push on the "and" — does not move the grid and
# does not count against it the way random timing does, though it still
# counts toward the re-acquire streak, because a grid that has landed on
# the offbeats sees every real beat as exactly that.
TIGHT_WINDOW = 0.15
TIGHT_FIT = 1.0
SLOPPY_FIT = 0.5
SUBDIVISION_FIT = 0.7
SUBDIVISION_TOLERANCE = 0.08    # a real swung "and" wanders from 0.60 to 0.75 of the beat
ACQUIRE_ONSETS = 16             # how far back the first lock looks for its anchor
REACQUIRE_ONSETS = 6            # a re-acquire follows the run that contradicted the grid

# Rubato: the local period over the last few on-grid onsets, relative to
# the global one. Inside the deadband it is timing noise and the grid
# ignores it; beyond, the predicted beats stretch with it, up to the limit,
# and the base tempo itself drifts after it — so a momentary push or pull
# is absorbed, while a ritardando that keeps going becomes the new tempo.
RUBATO_ONSETS = 3
RUBATO_DEADBAND = 0.03
RUBATO_LIMIT = 0.25
RUBATO_ALPHA = 0.6
RUBATO_TEMPO_FOLLOW = 0.3

# Swing is read, not assumed: an "and" that keeps landing at two thirds of
# the beat is a swing feel, at a half it is straight, and the drums should
# put their own offbeats where the pianist puts theirs.
SWING_ZONE = (0.42, 0.78)
SWING_ALPHA = 0.15

# Once locked, confidence is how well the predicted grid is landing on the
# onsets — because that is what the drummer needs to know — tempered by
# regularity, so free playing that has stopped being a pulse loses the lock
# even while some onsets still fall near the grid by chance. Periodicity
# support earns the lock in the first place and decides changes of tempo;
# it is deliberately kept out of the held confidence, because a tempo
# bending under a ritardando smears the periodicity while the grid, bent
# with it, still fits and the gaps stay regular.
GRID_FIT_ONSETS = 8

# Silence handling: hold steady through a phrase gap, lose faith quickly
# after that, and stop predicting entirely once the player has clearly left.
# The grace sits late on purpose: the Listener's phrase fade owns the musical
# dropout, and this decay is the safety net behind it, not the performer.
SILENCE_GRACE_S = 3.5
SILENCE_UNLOCK_S = 4.5
DECAY_PER_S = 0.05

# Downbeat inference. Accent evidence lands in a per-bar-phase bucket when an
# onset sits close enough to the grid, and the contest is judged bar by bar:
# a phase must win each of several consecutive bars outright before beat 1
# moves onto it. Judging fresh bars rather than a decayed running total is
# what makes one sforzando harmless — it wins its own bar and then has
# nothing left — while a real accent pattern wins every bar and takes over.
ACCENT_GRID_WINDOW = 0.25       # fraction of a period an onset may sit off-grid
# A bar votes only if it held a contest: accent on at least two of its beats.
# An absolute evidence floor was tried and failed on real hands — a gentle
# pianist's whole bar weighs less than one forte chord, so the bar phase sat
# a beat wrong for a whole song — and the streak below already makes a lone
# sforzando harmless.
VOTE_MIN_BEATS = 2
ROTATE_DOMINANCE = 1.25         # winner must beat the incumbent by this ratio
ROTATE_BARS = 3                 # consecutive winning bars before beat 1 moves
PROFILE_ALPHA = 0.4             # smoothing for the diagnostic phase profile


@dataclass(frozen=True)
class BeatEvent:
    """One predicted beat on the caller's clock."""

    time_s: float
    bpm: float
    period_s: float
    beat_in_bar: int    # 1-based
    bar_index: int


@dataclass(frozen=True)
class BeatState:
    """Snapshot of what the tracker currently believes."""

    bpm: float | None
    confidence: float
    locked: bool
    beat_in_bar: int
    bar_index: int
    last_onset_s: float | None
    alternatives: tuple[float, ...] = ()    # runner-up tempi, in BPM
    rubato: float = 1.0                     # local period over global; above 1 is slowing
    swing: float = 0.5                      # where the "and" falls: 0.5 straight, 0.67 triplet


class BeatTracker:
    """Onset times in, predicted beats out."""

    def __init__(
        self,
        min_bpm: float = 50.0,
        max_bpm: float = 180.0,
        beats_per_bar: int = 4,
        min_onset_gap_s: float = 0.05,
        infer_downbeat: bool = True,
        preferred_bpm: float = 100.0,
        tempo_hint: float | None = None,
        hold: float | None = None,
    ) -> None:
        if not 0.0 < min_bpm < max_bpm:
            raise ValueError("need 0 < min_bpm < max_bpm")
        self._hold = max(0.0, min(1.0, float(hold or 0.0)))
        h = self._hold
        self._nudge = PHASE_NUDGE * (1.0 - HOLD_NUDGE * h)
        self._nudge_rubato = PHASE_NUDGE_RUBATO * (1.0 - HOLD_NUDGE * h)
        self._nudge_window = PHASE_NUDGE_WINDOW * (1.0 - HOLD_WINDOW * h)
        self._offgrid_reset = OFFGRID_RESET_STREAK + round(HOLD_STREAK * h)
        self._offgrid_fit = HOLD_OFFGRID_FIT * h
        self._rubato_limit = RUBATO_LIMIT * (1.0 - HOLD_RUBATO * h)
        self._tempo_follow = RUBATO_TEMPO_FOLLOW * (1.0 - HOLD_RUBATO * h)
        if beats_per_bar < 1:
            raise ValueError("beats_per_bar must be at least 1")
        if preferred_bpm <= 0:
            raise ValueError("preferred_bpm must be positive")
        if tempo_hint is not None and tempo_hint <= 0:
            raise ValueError("tempo_hint must be positive")
        self._min_bpm = float(min_bpm)
        self._max_bpm = float(max_bpm)
        self._tempo_hint = float(tempo_hint) if tempo_hint else None
        if self._tempo_hint:
            # A declared tempo may sit outside the by-ear range — a fast
            # waltz in three at 190 — and the range must let it be found.
            self._min_bpm = min(self._min_bpm, self._tempo_hint / 1.3)
            self._max_bpm = max(self._max_bpm, self._tempo_hint * 1.3)
        self._preferred_bpm = self._tempo_hint or float(preferred_bpm)
        self._prior_width = HINT_PRIOR_WIDTH if self._tempo_hint else None
        if self._tempo_hint:
            beat_s = 60.0 / self._tempo_hint
            self._silence_grace_s = max(SILENCE_GRACE_S, HINT_SILENCE_GRACE_BEATS * beat_s)
            self._silence_unlock_s = max(SILENCE_UNLOCK_S, HINT_SILENCE_UNLOCK_BEATS * beat_s)
        else:
            self._silence_grace_s = SILENCE_GRACE_S
            self._silence_unlock_s = SILENCE_UNLOCK_S
        self._beats_per_bar = int(beats_per_bar)
        self._min_onset_gap_s = float(min_onset_gap_s)
        self._infer_requested = bool(infer_downbeat)
        self._infer_downbeat = self._infer_requested and self._beats_per_bar > 1

        self._onset_times: deque[float] = deque(maxlen=64)
        self._onset_weights: deque[float] = deque(maxlen=64)
        self._last_onset_s: float | None = None
        self._last_emitted_beat_s: float | None = None
        self._next_beat_s: float | None = None
        self._last_advance_s: float | None = None

        # Tempo: the active hypothesis, the runners-up, and the challenger
        # currently trying to unseat it.
        self._active_period: float | None = None
        self._hypotheses: tuple[TempoHypothesis, ...] = ()
        self._challenger_period: float | None = None
        self._challenger_streak = 0
        self._lock_candidate: float | None = None
        self._lock_streak = 0
        self._bpm: float | None = None
        self._confidence = 0.0
        self._locked = False
        self._beat_counter = 0
        self._offgrid_streak = 0

        # Rubato: recent (onset, grid point) pairs and the smoothed ratio.
        self._grid_points: deque[tuple[float, float]] = deque(maxlen=RUBATO_ONSETS)
        self._rubato = 1.0
        # Swing: where the pianist's "and" actually falls, read from the
        # off-grid onsets that sit in the half-to-two-thirds zone.
        self._swing = 0.5

        # Evidence from the periodicity ranking, and whether recent onsets
        # landed on the grid; confidence is drawn from one or the other.
        self._evidence = 0.0
        self._grid_fit: deque[float] = deque(maxlen=GRID_FIT_ONSETS)

        # Downbeat inference: which raw counter phase is beat 1, the current
        # bar's accent evidence, a smoothed profile for diagnostics, and the
        # hysteresis for changing our mind.
        self._bar_phase = 0
        self._bar_accent = [0.0] * self._beats_per_bar
        self._phase_ema = [0.0] * self._beats_per_bar
        self._phase_candidate: int | None = None
        self._phase_streak = 0
        self._beats_since_bar = 0
        self._last_cluster_phase: int | None = None
        # The first onset of a stretch of playing. People start on the one,
        # so the grid is numbered from it at lock, until the accents object.
        self._entry_s: float | None = None

        # Accent per absolute beat index, kept for a while so a meter scorer
        # can look back over the last few bars whatever the bar length is.
        self._accent_log: dict[int, float] = {}
        self._last_cluster_index: int | None = None

        # Accepted onsets, after merging. Read by status lines and tests.
        self.onsets = 0

    # what the tracker believes

    @property
    def hold(self) -> float:
        return self._hold

    @property
    def beats_per_bar(self) -> int:
        return self._beats_per_bar

    @property
    def hypotheses(self) -> tuple[TempoHypothesis, ...]:
        """The current tempo ranking, best first. For eyes and tests."""
        return self._hypotheses

    @property
    def phase_profile(self) -> tuple[float, ...]:
        """Smoothed accent evidence per bar phase, beat-1-first. For eyes and tests."""
        return tuple(
            self._phase_ema[(self._bar_phase + i) % self._beats_per_bar]
            for i in range(self._beats_per_bar)
        )

    def _numbering(self, counter: int) -> tuple[int, int]:
        beat_in_bar = (counter - self._bar_phase) % self._beats_per_bar + 1
        bar_index = max(counter - self._bar_phase, 0) // self._beats_per_bar
        return beat_in_bar, bar_index

    @property
    def state(self) -> BeatState:
        beat_in_bar, bar_index = self._numbering(self._beat_counter)
        alternatives = tuple(
            round(h.bpm, 1) for h in self._hypotheses
            if self._active_period is None or not same_period(h.period_s, self._active_period)
        )
        return BeatState(
            bpm=self._bpm,
            confidence=self._confidence,
            locked=self._locked,
            beat_in_bar=beat_in_bar,
            bar_index=bar_index,
            last_onset_s=self._last_onset_s,
            alternatives=alternatives,
            rubato=self._rubato,
            swing=self._swing,
        )

    def set_meter(self, beats_per_bar: int, downbeat_index: int | None = None) -> None:
        """Change the bar length live.

        downbeat_index is an absolute beat index (the counter's units) that
        is, or will be, beat 1. Without it the current beat 1 residue is kept
        as far as the new bar length allows. Accent bookkeeping for the old
        bar is discarded; the per-beat accent log is not, so a meter scorer
        keeps its evidence across the change.
        """
        if beats_per_bar < 1:
            raise ValueError("beats_per_bar must be at least 1")
        m = int(beats_per_bar)
        self._beats_per_bar = m
        self._infer_downbeat = self._infer_requested and m > 1
        if downbeat_index is not None:
            self._bar_phase = int(downbeat_index) % m
        else:
            self._bar_phase %= m
        self._bar_accent = [0.0] * m
        self._phase_ema = [0.0] * m
        self._phase_candidate = None
        self._phase_streak = 0
        self._beats_since_bar = 0
        self._last_cluster_phase = None

    def accent_history(self, beats: int) -> list[tuple[int, float]]:
        """Accent per absolute beat for the last `beats` emitted beats.

        Beats nobody played on read as 0.0 — silence on a beat is evidence
        too, which is why the log is dense and not just a list of onsets.
        """
        end = self._beat_counter
        start = max(0, end - int(beats))
        return [(i, self._accent_log.get(i, 0.0)) for i in range(start, end)]

    # input

    def on_onset(self, t_s: float, accent: float = 1.0) -> bool:
        """Feed one onset. Returns False when it merged into the previous one.

        A chord arrives as several note-ons a few milliseconds apart; only the
        first carries timing information, so the rest merge — but their accent
        still counts, toward the cluster's weight in the tempo evidence and
        toward its bar-phase bucket, because a big chord is a stronger claim
        about where the beat and the bar are than a single note.
        """
        t_s = float(t_s)
        accent = max(float(accent), 0.0)
        if (self._last_onset_s is not None
                and t_s - self._last_onset_s < self._min_onset_gap_s):
            self._merge_accent(accent)
            return False
        self._onset_times.append(t_s)
        self._onset_weights.append(sqrt(max(accent, 0.05)))
        if self._entry_s is None:
            self._entry_s = t_s
        self._last_onset_s = t_s
        self.onsets += 1
        if not self._count_in():
            self._update_tempo_estimate()
        self._update_phase_from_onset(t_s)
        self._refresh_confidence()
        self._note_accent(t_s, accent)
        return True

    def credit_last_cluster(self, accent: float) -> None:
        """Bank accent that was only knowable once the last cluster was complete.

        A listener judges some things — an open root under a chord, a bass
        line moving — only when the cluster's last note is in, which may be
        after the first note has already been fed here. This lands the late
        credit where that cluster's own notes went.
        """
        self._merge_accent(max(float(accent), 0.0))

    def _merge_accent(self, accent: float) -> None:
        if accent <= 0.0:
            return
        if self._onset_weights:
            w = self._onset_weights[-1]
            self._onset_weights[-1] = sqrt(w * w + accent)
        if self._last_cluster_phase is not None:
            self._bar_accent[self._last_cluster_phase] += accent
        if self._last_cluster_index is not None:
            self._accent_log[self._last_cluster_index] = (
                self._accent_log.get(self._last_cluster_index, 0.0) + accent)

    def _count_in(self) -> bool:
        """With a declared tempo, a couple of gaps at it are enough to start."""
        if (self._tempo_hint is None or self._active_period is not None
                or len(self._onset_times) < COUNT_IN_GAPS + 1):
            return False
        beat = 60.0 / self._tempo_hint
        times = list(self._onset_times)[-(COUNT_IN_GAPS + 1):]
        for gap in (b - a for a, b in zip(times, times[1:])):
            multiple = round(gap / beat * 2.0) / 2.0     # halves of a beat
            if not 0.5 <= multiple <= 4.0:
                return False
            if abs(gap - multiple * beat) > max(COUNT_IN_TOLERANCE * multiple * beat,
                                                 REGULARITY_FLOOR_S):
                return False
        self._active_period = beat
        self._bpm = self._tempo_hint
        self._evidence = COUNT_IN_EVIDENCE
        self._confidence = COUNT_IN_EVIDENCE
        self._lock_candidate, self._lock_streak = None, 0
        self._locked = True
        self._next_beat_s = self._acquire_phase(beat)
        return True

    def _refresh_confidence(self) -> None:
        if self._locked and len(self._grid_fit) >= 3:
            fit = sum(self._grid_fit) / len(self._grid_fit)
            regular = self._regularity(self._grid_period(), REGULARITY_TOLERANCE_HOLD)
            self._confidence = fit * sqrt(min(1.0, regular / LOCK_REGULARITY))
        elif self._active_period is not None:
            regular = self._regularity(self._active_period, REGULARITY_TOLERANCE_LOCK)
            self._confidence = self._evidence * sqrt(min(1.0, regular / LOCK_REGULARITY))
        else:
            self._confidence = self._evidence
        self._settle_lock()

    def _regularity(self, period: float, tolerance: float) -> float:
        """Share of recent onset gaps that are a simple multiple of the period."""
        if period <= 0.0:
            return 0.0
        times = list(self._onset_times)[-(REGULARITY_IOIS + 1):]
        if len(times) < 3:
            return 0.0
        gaps = [b - a for a, b in zip(times, times[1:])]
        explained = 0.0
        for i, gap in enumerate(gaps):
            # A whole number of periods, or a repeat of a recent gap, is
            # strong evidence. A lone subdivision is weaker: at a slow
            # candidate period the subdivisions blanket the range random
            # gaps live in, and a real rhythm's subdivisions repeat anyway.
            if any(abs(gap - m * period) <= max(tolerance * m * period, REGULARITY_FLOOR_S)
                   for m in REGULARITY_MULTIPLES if m >= 1.0):
                explained += 1.0
            elif any(abs(gap - gaps[j]) <= max(tolerance * gap, REGULARITY_FLOOR_S)
                     for j in (i - 1, i - 2) if j >= 0):
                explained += 1.0
            elif any(abs(gap - m * period) <= max(tolerance * m * period, REGULARITY_FLOOR_S)
                     for m in REGULARITY_MULTIPLES if m < 1.0):
                explained += SUBDIVISION_REGULARITY
        return explained / len(gaps)

    def advance(self, now_s: float) -> list[BeatEvent]:
        """Decay stale confidence, then emit every beat due by now_s.

        A caller scheduling ahead passes now + lead; BeatEvent.time_s is
        always the true grid time, the caller just learns it early.
        """
        dt = 0.0 if self._last_advance_s is None else max(0.0, now_s - self._last_advance_s)
        self._last_advance_s = now_s

        if self._last_onset_s is not None:
            silence_s = now_s - self._last_onset_s
            if silence_s > self._silence_grace_s and dt > 0.0:
                self._confidence *= DECAY_PER_S ** dt
            if silence_s > self._silence_unlock_s and self._locked:
                self._locked = False
                self._next_beat_s = None
                self._offgrid_streak = 0
                self._rubato = 1.0
                self._grid_points.clear()
                self._grid_fit.clear()
                self._evidence = self._confidence
                self._last_cluster_phase = None
                self._last_cluster_index = None
                # A part-filled bar of accents is stale once the grid is gone.
                self._bar_accent = [0.0] * self._beats_per_bar
                self._beats_since_bar = 0
                self._phase_candidate = None
                self._phase_streak = 0
                self._entry_s = None      # whatever comes next is a new entry

        return self._emit_due_beats(now_s)

    # tempo

    def _update_tempo_estimate(self) -> None:
        onsets = list(zip(self._onset_times, self._onset_weights))
        always = (self._active_period,) if self._active_period is not None else ()
        if self._tempo_hint:
            always = always + (60.0 / self._tempo_hint,)
        hypotheses = rank_periods(onsets, self._min_bpm, self._max_bpm,
                                  self._preferred_bpm, always=always,
                                  prior_width=self._prior_width)
        self._hypotheses = tuple(hypotheses)
        if not hypotheses:
            return
        top = hypotheses[0]
        in_window = sum(1 for t, _ in onsets if t >= onsets[-1][0] - 6.0)
        strength = min(1.0, in_window / FULL_EVIDENCE_ONSETS)

        if self._active_period is None:
            # The ranking proper is the first few by score; a best-supported
            # extra may ride along after them, and it only matters to a hint.
            ranked = hypotheses[:TOP_HYPOTHESES]
            near_top = [h for h in ranked if h.score >= NEAR_TOP_SCORE * top.score]
            top = max(near_top, key=lambda h: h.support)
            strongest = max(hypotheses, key=lambda h: h.support)
            if self._overrules_hint(strongest, top):
                top = strongest
            supported = top.support * strength
            regular = self._regularity(top.period_s, REGULARITY_TOLERANCE_LOCK)
            worthy = self._earns_lock(top.support, regular, strength, top.period_s)
            if (worthy and self._lock_candidate is not None
                    and abs(top.period_s - self._lock_candidate)
                    <= LOCK_CANDIDATE_TOLERANCE * self._lock_candidate):
                self._lock_streak += 1
                self._lock_candidate += 0.5 * (top.period_s - self._lock_candidate)
            elif worthy:
                self._lock_candidate, self._lock_streak = top.period_s, 1
            else:
                self._lock_candidate, self._lock_streak = None, 0
            needed = self._streak_needed(supported)
            enough = MIN_ONSETS_TO_LOCK
            if self._near_hint(top.period_s):
                needed, enough = min(needed, HINT_LOCK_STREAK), HINT_MIN_ONSETS
            self._evidence = supported * min(1.0, self._lock_streak / needed)
            if self._lock_streak >= needed and len(onsets) >= enough:
                self._lock_candidate, self._lock_streak = None, 0
                self._adopt(top)
            return

        active = next((h for h in hypotheses
                       if same_period(h.period_s, self._active_period)), None)
        # Under a hint, the prior may rank the pianist's real period below
        # the hint's favourite; overwhelming support for it overrules that.
        strongest = max(hypotheses, key=lambda h: h.support)
        overwhelming = (
            active is not None
            and not same_period(strongest.period_s, self._active_period)
            and self._overrules_hint(strongest, active)
        )
        if overwhelming:
            top = strongest
        elif self._active_period is not None:
            top = self._continuous(top, hypotheses)
        if active is not None and same_period(top.period_s, self._active_period):
            # The incumbent still leads: follow its refined period with inertia.
            self._challenger_period = None
            self._challenger_streak = 0
            alpha = TEMPO_ALPHA_LOCKED if self._locked else TEMPO_ALPHA_FREE
            self._active_period += alpha * (top.period_s - self._active_period)
            self._bpm = 60.0 / self._active_period
            self._evidence = top.support
            return

        # Someone else leads. Count how long they keep it up — unless the
        # grid is fitting, in which case the window is simply behind. The
        # exception is a wrong tempo hint: a misfit grid can look like it
        # fits when the pianist's onsets land on its subdivisions, and only
        # overwhelming evidence for another period sees through that.
        self._evidence = active.support if active is not None else self._evidence * 0.7
        fit = (sum(self._grid_fit) / len(self._grid_fit)) if len(self._grid_fit) >= 3 else 0.0
        if self._locked and fit >= CHALLENGER_FIT_CEILING and not overwhelming:
            self._challenger_period = None
            self._challenger_streak = 0
            return
        if (self._challenger_period is not None
                and same_period(top.period_s, self._challenger_period)):
            self._challenger_streak += 1
        else:
            self._challenger_period = top.period_s
            self._challenger_streak = 1
        active_score = active.score if active is not None else 0.0
        dominance = CHALLENGER_DOMINANCE
        if self._tempo_hint and not self._near_hint(top.period_s):
            dominance = HINT_CHALLENGER_DOMINANCE
        if (self._challenger_streak >= CHALLENGER_STREAK
                and (top.score >= dominance * active_score or overwhelming)):
            self._adopt(top)

    def _continuous(self, top: TempoHypothesis,
                    hypotheses: list[TempoHypothesis]) -> TempoHypothesis:
        """Among octave-equivalent near-top readings, the one nearest the tempo now.

        A pianist who has accelerated from 100 to 136 is at 136, not at 68,
        however the prior ranks those two; the beat is the level that was
        being followed.
        """
        if self._active_period is None:
            return top
        best, best_gap = top, abs(log(top.period_s / self._active_period))
        for h in hypotheses:
            if h is top or h.support < OCTAVE_EQUIVALENCE * top.support:
                continue
            ratio = h.period_s / top.period_s
            if not any(abs(ratio - m) <= OCTAVE_TOLERANCE * m for m in OCTAVE_RATIOS):
                continue
            gap = abs(log(h.period_s / self._active_period))
            if gap < best_gap:
                best, best_gap = h, gap
        return best

    def _near_hint(self, period_s: float) -> bool:
        if not self._tempo_hint:
            return False
        hint_period = 60.0 / self._tempo_hint
        return abs(period_s - hint_period) <= HINT_BAND * hint_period

    def _related_to_hint(self, period_s: float) -> bool:
        """Whether a period is the hint or a simple multiple or subdivision of it."""
        if not self._tempo_hint:
            return False
        hint_period = 60.0 / self._tempo_hint
        return any(abs(period_s - m * hint_period) <= HINT_RELATED_TOLERANCE * m * hint_period
                   for m in HINT_RELATED)

    def _overrules_hint(self, strongest: TempoHypothesis, favourite: TempoHypothesis) -> bool:
        """Evidence for an unrelated period so strong the hint must yield."""
        return (self._tempo_hint is not None
                and not self._related_to_hint(strongest.period_s)
                and strongest.support >= HINT_OVERRIDE_SUPPORT
                and favourite.support <= HINT_OVERRIDE_RATIO * strongest.support)

    @staticmethod
    def _streak_needed(supported: float) -> int:
        """Consecutive wins a candidate needs, fewer the better supported."""
        if supported >= STRONG_SUPPORT:
            return LOCK_STREAK_STRONG
        if supported <= LOCK_CONFIDENCE:
            return LOCK_STREAK
        span = STRONG_SUPPORT - LOCK_CONFIDENCE
        extra = (STRONG_SUPPORT - supported) / span * (LOCK_STREAK - LOCK_STREAK_STRONG)
        return min(LOCK_STREAK, LOCK_STREAK_STRONG + ceil(extra - 1e-9))

    def _earns_lock(self, support: float, regular: float, strength: float = 1.0,
                    period_s: float | None = None) -> bool:
        """The one place that says what evidence is enough to commit a grid."""
        if period_s is not None and self._near_hint(period_s):
            if support >= HINT_LOCK_CONFIDENCE and regular >= HINT_LOCK_REGULARITY:
                return True
        if support * strength >= LOCK_CONFIDENCE and regular >= LOCK_REGULARITY:
            return True
        return strength >= 1.0 and support >= RUN_SUPPORT and regular >= RUN_REGULARITY

    def _settle_lock(self) -> None:
        """Lock and unlock with hysteresis, acquiring a grid on the way in."""
        if self._locked:
            if self._confidence < UNLOCK_CONFIDENCE:
                self._locked = False
                self._next_beat_s = None
                self._grid_points.clear()
                self._grid_fit.clear()
                self._rubato = 1.0
                self._evidence = self._confidence
        elif (len(self._onset_times) >= MIN_ONSETS_TO_LOCK
                and self._active_period is not None):
            regular = self._regularity(self._active_period, REGULARITY_TOLERANCE_LOCK)
            if self._earns_lock(self._evidence, regular, period_s=self._active_period):
                self._locked = True
                if self._next_beat_s is None:
                    self._next_beat_s = self._acquire_phase(self._active_period)
                self._number_from_entry()

    def _adopt(self, hypothesis: TempoHypothesis) -> None:
        """Make this hypothesis the one the grid follows."""
        level_change = (self._active_period is not None
                        and not same_period(hypothesis.period_s, self._active_period))
        self._active_period = hypothesis.period_s
        self._bpm = 60.0 / hypothesis.period_s
        self._evidence = hypothesis.support
        self._confidence = hypothesis.support
        self._challenger_period = None
        self._challenger_streak = 0
        self._rubato = 1.0
        self._grid_points.clear()
        self._grid_fit.clear()
        self._offgrid_streak = 0
        regular = self._regularity(hypothesis.period_s, REGULARITY_TOLERANCE_LOCK)
        self._locked = self._earns_lock(hypothesis.support, regular, period_s=hypothesis.period_s)
        self._next_beat_s = self._acquire_phase(hypothesis.period_s) if self._locked else None
        if self._locked:
            self._number_from_entry()
        if level_change:
            # Beat indices mean something else at a different tempo, so the
            # bar-phase evidence and the per-beat log start over.
            self._accent_log.clear()
            self._last_cluster_index = None
            self._last_cluster_phase = None
            self._bar_accent = [0.0] * self._beats_per_bar
            self._phase_ema = [0.0] * self._beats_per_bar
            self._phase_candidate = None
            self._phase_streak = 0
            self._beats_since_bar = 0

    def _number_from_entry(self) -> None:
        """Number the grid so the entry onset is beat 1.

        Nobody counts in and then starts on the "and of three": the first
        note of a stretch of playing is a downbeat far more often than any
        other beat. That is only a prior — an anacrusis proves it wrong — so
        the accent contest keeps the last word, and one entry is spent once
        it has been used, so a re-lock later in the piece leaves the bar
        where the accents put it.
        """
        if (not self._infer_downbeat or self._entry_s is None
                or self._next_beat_s is None or self._active_period is None):
            return
        k = round((self._next_beat_s - self._entry_s) / self._grid_period())
        self._bar_phase = (self._beat_counter - k) % self._beats_per_bar
        self._entry_s = None

    def _acquire_phase(self, period: float, recent: int = ACQUIRE_ONSETS) -> float:
        """Where the grid goes at lock: on the onset most others agree with.

        The onset that happened to tip the evidence over the line may be a
        push on the "and"; anchoring there would put every beat on the
        offbeats until the re-acquire kicks in. So each recent onset is tried
        as an anchor and the one the most onsets sit on wins, most recent
        first among equals. The result is rolled up to the grid point nearest
        the latest onset so emission starts now, not a bar ago, and past any
        beat already emitted so no beat is ever emitted twice.
        """
        times = list(self._onset_times)[-recent:]
        weights = list(self._onset_weights)[-len(times):]
        best_anchor, best_support = times[-1], -1.0
        for anchor in reversed(times):
            # Weighted by accent, so the beats of a swing feel outvote the
            # swung eighths that follow each of them and would otherwise tie.
            support = 0.0
            for t, w in zip(times, weights):
                k = round((t - anchor) / period)
                if abs(t - (anchor + k * period)) <= 0.15 * period:
                    support += w
            if support > best_support + 1e-9:
                best_anchor, best_support = anchor, support
        latest = times[-1]
        grid = best_anchor + period * round((latest - best_anchor) / period)
        if self._last_emitted_beat_s is not None:
            while grid <= self._last_emitted_beat_s + 0.5 * period:
                grid += period
        return grid

    # phase

    def _grid_period(self) -> float:
        """The period the grid actually steps by: global tempo, bent by rubato."""
        base = 60.0 / self._bpm
        if abs(self._rubato - 1.0) > RUBATO_DEADBAND:
            return base * self._rubato
        return base

    def _update_phase_from_onset(self, onset_s: float) -> None:
        if not self._locked or self._bpm is None:
            return

        period = self._grid_period()
        if self._next_beat_s is None:
            self._next_beat_s = onset_s
            return

        nearest_index = round((onset_s - self._next_beat_s) / period)
        nearest_time = self._next_beat_s + nearest_index * period
        phase_error = onset_s - nearest_time

        if abs(phase_error) > self._nudge_window * period:
            offset = (phase_error / period) % 1.0
            on_subdivision = any(abs(offset - f) <= SUBDIVISION_TOLERANCE
                                 for f in (0.5, 1.0 / 3.0, 2.0 / 3.0))
            self._grid_fit.append(SUBDIVISION_FIT if on_subdivision else self._offgrid_fit)
            if on_subdivision and SWING_ZONE[0] <= offset <= SWING_ZONE[1]:
                self._swing += SWING_ALPHA * (offset - self._swing)
            self._offgrid_streak += 1
            if self._offgrid_streak < self._offgrid_reset:
                return      # syncopation: the flywheel does not follow it
            # The grid was wrong. Re-acquire where the weight of the last
            # few onsets says the pulse is — the run that just contradicted
            # the grid, and a little context — which need not be this onset.
            self._offgrid_streak = 0
            self._grid_points.clear()
            self._rubato = 1.0
            self._next_beat_s = self._acquire_phase(60.0 / self._bpm, recent=REACQUIRE_ONSETS)
            return
        self._offgrid_streak = 0
        if abs(phase_error) <= TIGHT_WINDOW * period:
            self._grid_fit.append(TIGHT_FIT)
            self._grid_points.append((onset_s, nearest_time))
            self._update_rubato()
        else:
            self._grid_fit.append(SLOPPY_FIT)

        nudge = self._nudge_rubato if abs(self._rubato - 1.0) > RUBATO_DEADBAND else self._nudge
        corrected = nearest_time + phase_error * nudge
        if self._last_emitted_beat_s is not None:
            # Half a period, not zero: an onset trailing an already-emitted
            # beat by a few milliseconds lands `corrected` a hair after that
            # beat, and a zero floor would accept it, emit a duplicate beat,
            # and shift the counter-to-time mapping under the bar numbering.
            while corrected <= self._last_emitted_beat_s + 0.5 * period:
                corrected += period

        self._next_beat_s = corrected

    def _update_rubato(self) -> None:
        """Local period over the last few on-grid onsets, against the global one."""
        if len(self._grid_points) < RUBATO_ONSETS or self._bpm is None:
            return
        base = 60.0 / self._bpm
        (t0, g0), (t1, g1) = self._grid_points[0], self._grid_points[-1]
        steps = round((g1 - g0) / self._grid_period())
        if steps < 2:
            return      # one interval is timing, not tempo
        local = (t1 - t0) / steps
        ratio = max(1.0 - self._rubato_limit, min(1.0 + self._rubato_limit, local / base))
        self._rubato += RUBATO_ALPHA * (ratio - self._rubato)
        if abs(self._rubato - 1.0) > RUBATO_DEADBAND and self._active_period is not None:
            # Sustained: let the tempo itself drift after the playing, so the
            # ratio re-centres and the stretch never has to saturate.
            self._active_period += self._tempo_follow * (local - self._active_period)
            self._bpm = 60.0 / self._active_period

    # accents and the bar

    def _note_accent(self, t_s: float, accent: float) -> None:
        """Bank this cluster's accent against the beat it sits on."""
        self._last_cluster_phase = None
        self._last_cluster_index = None
        if not (self._locked and self._bpm is not None and self._next_beat_s is not None):
            return
        period = self._grid_period()
        k = round((t_s - self._next_beat_s) / period)
        if abs(t_s - (self._next_beat_s + k * period)) > ACCENT_GRID_WINDOW * period:
            return      # off-grid pushes say nothing about where the bar is
        index = self._beat_counter + k
        self._accent_log[index] = self._accent_log.get(index, 0.0) + accent
        self._last_cluster_index = index
        if len(self._accent_log) > 256:
            horizon = self._beat_counter - 128
            self._accent_log = {i: a for i, a in self._accent_log.items() if i >= horizon}
        if self._infer_downbeat:
            phase = index % self._beats_per_bar
            self._bar_accent[phase] += accent
            self._last_cluster_phase = phase

    def _emit_due_beats(self, now_s: float) -> list[BeatEvent]:
        if not self._locked or self._bpm is None or self._next_beat_s is None:
            return []

        period = self._grid_period()
        events: list[BeatEvent] = []
        while self._next_beat_s <= now_s + 1e-6:
            beat_in_bar, bar_index = self._numbering(self._beat_counter)
            events.append(BeatEvent(
                time_s=self._next_beat_s,
                bpm=self._bpm,
                period_s=period,
                beat_in_bar=beat_in_bar,
                bar_index=bar_index,
            ))
            self._last_emitted_beat_s = self._next_beat_s
            self._beat_counter += 1
            self._next_beat_s += period
            if self._infer_downbeat:
                self._beats_since_bar += 1
                if self._beats_since_bar >= self._beats_per_bar:
                    self._beats_since_bar = 0
                    self._complete_accent_bar()
        return events

    def _complete_accent_bar(self) -> None:
        """Judge one bar's accent contest and move beat 1 only on a streak."""
        bar = self._bar_accent
        self._bar_accent = [0.0] * self._beats_per_bar
        for p in range(self._beats_per_bar):
            self._phase_ema[p] += PROFILE_ALPHA * (bar[p] - self._phase_ema[p])

        if sum(1 for a in bar if a > 0.0) < VOTE_MIN_BEATS:
            self._phase_candidate = None
            self._phase_streak = 0
            return
        winner = max(range(self._beats_per_bar), key=lambda p: bar[p])
        incumbent = bar[self._bar_phase]
        if winner == self._bar_phase or bar[winner] < ROTATE_DOMINANCE * incumbent:
            self._phase_candidate = None
            self._phase_streak = 0
            return
        if winner == self._phase_candidate:
            self._phase_streak += 1
        else:
            self._phase_candidate = winner
            self._phase_streak = 1
        if self._phase_streak >= ROTATE_BARS:
            self._bar_phase = winner
            self._phase_candidate = None
            self._phase_streak = 0
