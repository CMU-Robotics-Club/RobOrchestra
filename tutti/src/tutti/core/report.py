"""The pre-flight report: what will and will not play, before anyone presses go.

Answers the question the club currently answers by listening: can this
arrangement actually be performed by the bots we have, at the tempo we want?
"""

from __future__ import annotations

from .plan import Instrument, Plan, max_feasible_scale, plan_score
from .score import Score

MAX_DETAIL_LINES = 6


def _beat(time_s: float, bpm: float) -> float:
    return time_s * bpm / 60.0


def _describe(model) -> str:
    if model.voice_mode == "keyed":
        return f"{model.voices} keys, {model.max_rate_hz:.1f} hits/s per key"
    sticks = "stick" if model.voices == 1 else "sticks"
    return f"{model.voices} {sticks}, {model.max_rate_hz:.1f} hits/s"


def preflight(
    score: Score,
    instruments: dict[str, Instrument],
    binding: dict[int, list[str]],
    target_bpm: float | None = None,
    tolerance_ms: float = 15.0,
) -> list[str]:
    source_bpm = score.initial_bpm
    target_bpm = target_bpm or source_bpm
    scale = source_bpm / target_bpm
    plan = plan_score(score, instruments, binding, tolerance_ms, scale)

    out = [f"{score.name}: {len(score.events)} notes, {score.duration_s * scale:.1f}s "
           f"at {target_bpm:.0f} BPM (written {source_bpm:.0f})", ""]

    out.append("Bound parts:")
    roles = {p.part_id: p.role for p in score.parts}
    for part in score.parts:
        bots = binding.get(part.part_id, [])
        if not bots:
            out.append(f"  part {part.part_id} {part.role:<8} -> NOTHING BOUND")
            continue
        head = instruments[bots[0]]
        extra = f" (+{len(bots) - 1} more)" if len(bots) > 1 else ""
        out.append(f"  part {part.part_id} {part.role:<8} -> {head.bot_id:<14}"
                   f"({_describe(head.model)}){extra}")
    out.append("")

    out.append(f"Feasibility at {target_bpm:.0f} BPM:")
    for part in score.parts:
        pid = part.part_id
        hits = plan.for_part(pid)
        drops = plan.drops_for_part(pid)
        total = len(hits) + len(drops)
        if not total:
            continue

        nudged = [h for h in hits if abs(h.nudge_ms) > 1e-6]
        status = f"{total} notes"
        if drops:
            status += f", {len(drops)} infeasible"
        if nudged:
            status += f", {len(nudged)} nudged"
        if not drops and not nudged:
            status += ", all clear"
        out.append(f"  part {pid} {part.role:<8}: {status}")

        # Drops first: a shifted note is a detail, a missing one is a problem.
        shown = 0
        for d in drops:
            if shown >= MAX_DETAIL_LINES:
                break
            out.append(f"    t={d.requested_s:7.3f}s beat {_beat(d.requested_s, target_bpm):7.2f}"
                       f"  {d.detail}  -> DROP {d.reason}")
            shown += 1
        for h in nudged:
            if shown >= MAX_DETAIL_LINES:
                break
            out.append(f"    t={h.requested_s:7.3f}s beat {_beat(h.requested_s, target_bpm):7.2f}"
                       f"  nudge +{h.nudge_ms:.1f}ms  OK")
            shown += 1
        remaining = len(nudged) + len(drops) - shown
        if remaining > 0:
            out.append(f"    ... and {remaining} more")

    out.append("")
    if plan.feasible:
        out.append(f"  Playable as written at {target_bpm:.0f} BPM.")
    else:
        worst = _worst_part(plan)
        out.append(f"  NOT playable at {target_bpm:.0f} BPM: "
                   f"{len(plan.drops)} notes would be dropped.")
        if worst is not None:
            out.append(f"  Worst part: {worst[0]} ({worst[1]} drops), first at "
                       f"t={worst[2]:.3f}s.")

    floor = 0.2
    best_scale = max_feasible_scale(score, instruments, binding, tolerance_ms, lowest=floor)
    if best_scale == float("inf"):
        out.append("  No tempo works: something is unplayable regardless of speed.")
    elif best_scale <= floor:
        out.append(f"  Max feasible tempo: beyond {source_bpm / floor:.0f} BPM "
                   f"(this arrangement is nowhere near the fleet's limits)")
    else:
        out.append(f"  Max feasible tempo for this arrangement: "
                   f"{source_bpm / best_scale:.0f} BPM")
    return out


def _worst_part(plan: Plan) -> tuple[int, int, float] | None:
    counts: dict[int, list[float]] = {}
    for d in plan.drops:
        counts.setdefault(d.part_id, []).append(d.requested_s)
    if not counts:
        return None
    pid = max(counts, key=lambda k: len(counts[k]))
    return pid, len(counts[pid]), min(counts[pid])
