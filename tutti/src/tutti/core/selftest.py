"""A short fixed pattern for bringing up one bot.

Playing a whole song at a robot you have just wired up tells you very little.
This plays three things instead: separated single hits, so you can see it
trigger at all; a steady rhythm, so you can hear whether it is even; and a ramp
that speeds up past what the bot can physically do, so you hear where its limit
actually is rather than trusting the number in fleet.py.

The ramp is the useful one. It is also the fastest way to find out that a servo
needs recalibrating, because a stick that is set too deep starts missing long
before the planner says it should.
"""

from __future__ import annotations

from .plan import Instrument
from .score import NoteEvent, Part, Score

GM_SNARE = 38


def build_test_score(
    role: str = "snare",
    note: int = GM_SNARE,
    singles: int = 6,
    single_gap_s: float = 0.8,
    steady: int = 8,
    steady_hz: float = 4.0,
    ramp: int = 24,
    ramp_from_hz: float = 5.0,
    ramp_to_hz: float = 32.0,
    gap_s: float = 1.0,
) -> Score:
    """Singles, then a steady rhythm, then a ramp that outruns the bot."""
    events: list[NoteEvent] = []
    t = 0.5

    for _ in range(singles):
        events.append(NoteEvent(part_id=1, note=note, velocity=110, time_s=t))
        t += single_gap_s

    t += gap_s
    for _ in range(steady):
        events.append(NoteEvent(part_id=1, note=note, velocity=100, time_s=t))
        t += 1.0 / steady_hz

    t += gap_s
    for i in range(ramp):
        events.append(NoteEvent(part_id=1, note=note, velocity=100, time_s=t))
        # Sweep the rate geometrically so the speed-up sounds even.
        frac = i / max(ramp - 1, 1)
        hz = ramp_from_hz * (ramp_to_hz / ramp_from_hz) ** frac
        t += 1.0 / hz

    return Score(
        name=f"selftest:{role}",
        events=events,
        parts=[Part(part_id=1, role=role, notes=(note,))],
        initial_bpm=120.0,
    )


def describe(score: Score, instruments: dict[str, Instrument]) -> list[str]:
    out = [f"Self test for role {score.parts[0].role!r}, note {score.parts[0].notes[0]}",
           f"  {len(score.events)} hits over {score.duration_s:.1f}s"]
    for inst in instruments.values():
        out.append(f"  {inst.bot_id}: {inst.model.max_rate_hz:.1f} hits/s claimed, "
                   f"{inst.model.voices} voices, "
                   f"{inst.model.mech_latency_ms:.0f}ms travel")
    out.append("  singles, then steady, then a ramp that should outrun the bot")
    return out
