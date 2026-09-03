"""What the drummer hears in the pianist beyond the pulse.

The beat tracker answers "when"; this module answers "how". Three judgements,
all cheap and all incremental:

- **Dynamics.** A loudness EMA over velocities decides how hard the drums
  play. Note density — chords count once, a run counts per note-cluster —
  decides how *busy* they play, inversely: when the piano is a flurry the
  drums thin out to leave space, and when it settles into sustained chords
  they lean in. That inversion is most of what makes an accompanist feel
  like a bandmate instead of a backing track.

- **Phrases.** A short gap mid-performance is an invitation: the classic
  drummer move is to fill it. A longer silence is an ending: the drums fade
  over about a bar and rest, instead of hammering on alone. Both are read
  from the same silence clock, in beats rather than seconds so the behaviour
  scales with tempo.

- **Accents.** Each note contributes evidence about where the bar starts:
  velocity (squared, so loud stands out), how deep in the bass it sits, and
  whether the bass pitch class just changed, because harmony moves on
  downbeats far more often than off them. The tracker sums these per onset
  cluster and does the actual bar-phase inference; this module only scores.

Everything here is one thread's state, driven by the jam tick loop, and
pure enough to test with a hand-cranked clock.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

# Notes below this are "left hand" for accent purposes. E3: low enough that
# comped triads stay above it, high enough to catch real bass lines.
BASS_SPLIT = 52

# Accent weights. Velocity is squared so forte pokes out; depth is scaled by
# how far below the split the note sits; a bass pitch-class change is worth
# more than either because harmony motion is the strongest downbeat marker.
EXTRA_NOTE_WEIGHT = 0.25    # later notes of one cluster count less
MAX_DEPTH_BONUS = 1.2
CHANGE_BONUS = 0.6

CLUSTER_GAP_S = 0.05        # same threshold the beat tracker merges with

# Dynamics are both absolute and relative. The absolute level sets a
# baseline — a pianist who plays gently all evening gets gentler drums than
# one who hammers — but a pianist's loud is loud *for them*: one pair of
# hands on one instrument may never leave velocities 30 to 60, and the drums
# must still swell and hush with them. So a slow average of velocity is the
# player's own level, and the ratio of the current loudness to it shifts the
# baseline up or down.
LOUDNESS_ALPHA = 0.2
TYPICAL_ALPHA = 0.03                    # settles over a few dozen notes
DENSITY_WINDOW_S = 4.0
ABSOLUTE_EDGES = (0.30, 0.50, 0.70)     # loudness -> baseline intensity 1..4
SOFTER_RATIO = 0.75                     # loudness / typical below this: one down
LOUDER_RATIO = 1.15                     # above this: one up
MUCH_LOUDER_RATIO = 1.40                # above this: two up
# Schmitt thresholds in clusters per beat, so mode cannot flap on the fence.
# Two onsets a beat is ordinary comping — eighths, swing — and stays in
# groove; a flurry is three or more, a run of triplets or sixteenths.
SPARSE_ON, SPARSE_OFF = 2.6, 2.2
BUSY_ON, BUSY_OFF = 0.5, 0.7

# Phrases. Thresholds sit a fixed number of beats *beyond* the pianist's own
# typical gap between onset clusters (itself never less than a beat): someone
# comping every beat leaves a hole after two missed beats and has stopped
# after a bar of silence, someone playing eighths is judged the same way
# rather than twice as harshly, and someone padding whole notes is simply
# playing that way and gets neither a fill nor a fade-out for it.
GAP_FILL_LO = 0.8       # beats beyond typical: a hole begins
GAP_FILL_HI = 2.0       # and ends; past it the drummer just waits
FADE_START = 3.0        # beats beyond typical: the pianist has stopped
FADE_START_KEEPING_TIME = 7.0   # with a declared tempo: play through a rest
GAP_EMA_ALPHA = 0.3


@dataclass(frozen=True)
class Feel:
    """One reading of how the pianist is playing right now."""

    loudness: float         # velocity EMA, 0..1
    density: float          # onset clusters per beat
    intensity: int          # 0..4, what the groove should play at
    mode: str               # "sparse" | "groove" | "busy"
    velocity_scale: float   # 1.0 playing, falling through the fade-out
    resting: bool           # faded out entirely; schedule nothing
    gap_fill: bool          # one-shot: the pianist left a hole, fill it


class Listener:
    """Velocity and pitch stream in, Feel out, accents to the side."""

    def __init__(self, beats_per_bar: int = 4, keep_time: bool = False) -> None:
        # A drummer who knows the song plays through the piano's rests; one
        # who is following by ear stops when the pianist seems to have.
        self._fade_start_beats = FADE_START_KEEPING_TIME if keep_time else FADE_START
        self._fade_beats = float(max(beats_per_bar, 2))
        self._loudness: float | None = None
        self._typical: float | None = None
        self._cluster_times: deque[float] = deque(maxlen=64)
        self._mode = "groove"

        self._cluster_start_s: float | None = None
        self._cluster_bass_note: int | None = None
        self._prev_bass_pc: int | None = None
        self._change_credited = False

        self._last_cluster_s: float | None = None
        self._gap_ema_s: float | None = None
        self._gap_filled = False

    def set_meter(self, beats_per_bar: int) -> None:
        """The fade-out is one bar long, so it follows the bar."""
        self._fade_beats = float(max(int(beats_per_bar), 2))

    def on_note(self, note: int, velocity: int, t_s: float) -> float:
        """Absorb one note-on; returns its accent contribution for the tracker."""
        new_cluster = (self._cluster_start_s is None
                       or t_s - self._cluster_start_s >= CLUSTER_GAP_S)
        if new_cluster:
            if self._cluster_bass_note is not None:
                self._prev_bass_pc = self._cluster_bass_note % 12
            self._cluster_start_s = t_s
            self._cluster_bass_note = None
            self._change_credited = False
            self._cluster_times.append(t_s)
            if self._last_cluster_s is not None:
                gap = t_s - self._last_cluster_s
                if self._gap_ema_s is None:
                    self._gap_ema_s = gap
                else:
                    self._gap_ema_s += GAP_EMA_ALPHA * (gap - self._gap_ema_s)
            self._last_cluster_s = t_s
            self._gap_filled = False

        vel = max(1, min(127, int(velocity))) / 127.0
        if self._loudness is None:
            self._loudness = vel
            self._typical = vel
        else:
            self._loudness += LOUDNESS_ALPHA * (vel - self._loudness)
            self._typical += TYPICAL_ALPHA * (vel - self._typical)

        accent = (vel * vel) * (1.0 if new_cluster else EXTRA_NOTE_WEIGHT)
        if note < BASS_SPLIT:
            depth = min(MAX_DEPTH_BONUS, (BASS_SPLIT - note) / 16.0)
            accent += depth * (1.0 if new_cluster else EXTRA_NOTE_WEIGHT)
            pc = note % 12
            if self._cluster_bass_note is None or note < self._cluster_bass_note:
                self._cluster_bass_note = note
            if (not self._change_credited
                    and self._prev_bass_pc is not None
                    and pc != self._prev_bass_pc):
                accent += CHANGE_BONUS
                self._change_credited = True
        return accent

    def feel(self, now_s: float, period_s: float) -> Feel:
        """Read the current judgement. Safe to call every tick."""
        loudness = self._loudness if self._loudness is not None else 0.0

        while self._cluster_times and self._cluster_times[0] < now_s - DENSITY_WINDOW_S:
            self._cluster_times.popleft()
        window_s = DENSITY_WINDOW_S
        if self._cluster_times:
            window_s = min(DENSITY_WINDOW_S, max(now_s - self._cluster_times[0], 1.0))
        density = (len(self._cluster_times) / window_s) * period_s

        typical = self._typical if self._typical else loudness
        ratio = loudness / typical if typical > 0.0 else 1.0
        intensity = 1 + sum(1 for edge in ABSOLUTE_EDGES if loudness >= edge)
        if ratio < SOFTER_RATIO:
            intensity -= 1
        elif ratio >= MUCH_LOUDER_RATIO:
            intensity += 2
        elif ratio >= LOUDER_RATIO:
            intensity += 1
        intensity = max(0, min(4, intensity))

        # Mode follows density inversely, with hysteresis so a value sitting
        # on a threshold cannot flap bar to bar.
        if self._mode == "sparse":
            if density <= SPARSE_OFF:
                self._mode = "groove"
        elif self._mode == "busy":
            if density >= BUSY_OFF:
                self._mode = "groove"
        if self._mode == "groove":
            if density >= SPARSE_ON:
                self._mode = "sparse"
            elif density <= BUSY_ON and self._cluster_times:
                self._mode = "busy"
        if self._mode == "sparse":
            intensity = min(intensity, 2)   # thin *and* quieter: leave room

        velocity_scale, resting, gap_fill = 1.0, False, False
        if self._last_cluster_s is not None and period_s > 0:
            silence_beats = (now_s - self._last_cluster_s) / period_s
            typical_gap = max(1.0, (self._gap_ema_s or period_s) / period_s)
            if (not self._gap_filled
                    and typical_gap + GAP_FILL_LO <= silence_beats <= typical_gap + GAP_FILL_HI):
                gap_fill = True
                self._gap_filled = True
            fade_start = typical_gap + self._fade_start_beats
            if silence_beats > fade_start:
                velocity_scale = 1.0 - (silence_beats - fade_start) / self._fade_beats
                velocity_scale = max(0.0, velocity_scale)
                resting = velocity_scale <= 0.0

        return Feel(
            loudness=loudness,
            density=density,
            intensity=intensity,
            mode=self._mode,
            velocity_scale=velocity_scale,
            resting=resting,
            gap_fill=gap_fill,
        )
