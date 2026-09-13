"""Watch a conductor through the webcam and report every beat of the baton.

The same camera, hand tracking and predictive stroke detection as the
gesture source, with one difference in what a stroke means. Drumming in the
air, a downstroke is a hit and the screen is split into zones that decide
which drum. Conducting, a downstroke is a beat, wherever on the screen it
lands, and what it means is up to whoever is listening: a score player, an
improviser, a metronome.

The timing is what matters. The detector fires early — latency_ms before
the hand is predicted to land — and says when it expects the impact. That
impact moment, moved onto the ensemble's clock, is the beat: the notes on
it can be scheduled while the baton is still on its way down, which is the
only way a stick that takes 20 ms to travel arrives with the baton.

The old demo used a Pixy camera watching for a coloured baton to reverse
direction, on an Arduino writing "Beat" down a serial line. This needs no
baton, no Arduino and no serial port index, and lands the beat before the
hand does instead of a frame after.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from ..core.ensemble import Ensemble
from .gesture import GestureSource, _hand_state_ids

# How far from now a reported impact may be before it is treated as a
# timestamp mix-up rather than a prediction. The detector looks at most a
# quarter of a second ahead; anything beyond is not its number.
MAX_LEAD_S = 0.3
MAX_LAG_S = 0.1


class BatonSource(GestureSource):
    """Camera in, on_beat(impact_s, strength) out."""

    name = "baton"

    def __init__(
        self,
        on_beat: Callable[[float, float], None],
        model_path: Path | None = None,
        camera_index: int = 0,
        latency_ms: int = 90,
        detector: str = "predictive",
        mirror: bool = True,
        display: bool = True,
    ) -> None:
        super().__init__(model_path=model_path, camera_index=camera_index,
                         latency_ms=latency_ms, detector=detector,
                         mirror=mirror, display=display)
        self._on_beat = on_beat
        # Observation timestamps come from perf_counter in the capture loop;
        # tests substitute their own wall clock to drive synthetic frames.
        self._wall_ms: Callable[[], float] = lambda: time.perf_counter() * 1000.0
        self.status_text = ""

    def bind(self, ensemble: Ensemble) -> None:
        """Wire up detection with the whole frame as one zone."""
        cfg, tracking = self._config, self._tracking
        self._ensemble = ensemble
        self._zone_labels = ("CONDUCT",)
        self._zone_edges = ()
        self._zone_notes = {}
        self._zone_mapper = None
        self._zone_gate = tracking.ZoneHitGate(cooldown_ms=cfg.hit_zone_cooldown_ms)
        self._hand_states = tracking.HandStateStore(
            history_size=cfg.hit_history_size, gap_reset_ms=cfg.hand_gap_reset_ms)
        self._gesture_router = tracking.GestureRouter(
            label_to_command=cfg.gesture_to_command,
            cooldown_ms=cfg.gesture_command_cooldown_ms)
        self._detector = self._build_detector()

    def _process(self, observation) -> None:
        assert self._ensemble is not None, "bind() before _process()"
        self._hand_states.prune_stale(current_timestamp_ms=observation.timestamp_ms)

        hands = observation.hands[: self._config.max_hands]
        for hand, state_id in zip(hands, _hand_state_ids(hands)):
            hand_state = self._hand_states.get_or_create(
                state_id, hand.handedness, observation.timestamp_ms)
            hit = self._detector.update(
                hand_state=hand_state,
                landmarks=hand.landmarks,
                timestamp_ms=observation.timestamp_ms,
            )
            if hit is not None and self._zone_gate.should_emit(
                    zone="beat", timestamp_ms=hit.timestamp_ms):
                self.strikes += 1
                self._on_beat(self._impact_s(hit), float(hit.velocity))

            command = self._gesture_router.route(
                label=hand.top_gesture,
                handedness=hand.handedness,
                timestamp_ms=observation.timestamp_ms,
            )
            if command is not None:
                self._ensemble.command(command.command)

    def _impact_s(self, hit) -> float:
        """When the hand will land, on the ensemble's clock.

        The detector reports the impact on the capture clock; the difference
        between that and the capture clock now is how far ahead it is, and
        that lead is what the ensemble clock gets. A detector that does not
        predict (the legacy one) reports no impact, and the beat is now.
        """
        now = self._ensemble.now_s()
        if getattr(hit, "predicted_impact_ms", -1) < 0:
            return now
        lead_s = (hit.predicted_impact_ms - self._wall_ms()) / 1000.0
        return now + max(-MAX_LAG_S, min(MAX_LEAD_S, lead_s))

    def _overlay_status(self) -> str:
        return self.status_text or f"beats={self.strikes}"
