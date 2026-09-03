"""Walk a plan in real time and hand each hit to a transport before it is due.

The player never decides when a note sounds. It only decides when to pass the
note on, early enough that whatever is downstream can place it itself. That
split is the point: it is why the same code drives the speakers, the old daisy
chain, and eventually the bots over wifi.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from ..transports.base import Transport
from .plan import Plan, ScheduledHit

POLL_S = 0.002
MIN_LOOKAHEAD_S = 0.02
STALL_GRACE_S = 30.0


def default_clock(transport: Transport) -> Callable[[], float]:
    """Prefer the transport's own clock where it has one.

    Whatever makes the sound is the authority on what time it is. A sound card
    and the wall clock drift apart over a few minutes, and if the player trusts
    the wrong one it starts handing notes over late.
    """
    if hasattr(transport, "now_s"):
        return lambda: transport.now_s
    started = time.monotonic()
    return lambda: time.monotonic() - started


def play_plan(
    plan: Plan,
    transport: Transport,
    on_hit: Callable[[ScheduledHit], None] | None = None,
    tail_s: float = 1.0,
    clock: Callable[[], float] | None = None,
) -> int:
    """Play every hit in the plan. Returns how many were handed over.

    There is no speed argument on purpose. Playing an arrangement faster means
    replanning it, because the bots' limits do not scale with the tempo.
    """
    hits = sorted(plan.hits, key=lambda h: h.play_at_s)
    if not hits:
        return 0

    lookahead = max(transport.lookahead_s, MIN_LOOKAHEAD_S)
    now = clock or default_clock(transport)

    # A transport whose clock stops would otherwise spin here for ever. Watch
    # for the clock not advancing rather than for total elapsed time: a long
    # piece is not a stall, and a stopped sound card is one immediately.
    last_seen = now()
    last_moved = time.monotonic()

    def note_progress(current: float) -> bool:
        """Records the clock reading. False once it has been stuck too long."""
        nonlocal last_seen, last_moved
        if current != last_seen:
            last_seen = current
            last_moved = time.monotonic()
            return True
        return time.monotonic() - last_moved <= STALL_GRACE_S

    index = 0
    sent = 0
    while index < len(hits):
        current = now()
        horizon = current + lookahead
        due = []
        while index < len(hits) and hits[index].play_at_s <= horizon:
            due.append(hits[index])
            index += 1
        if due:
            sent += transport.send(due)
            if on_hit:
                for hit in due:
                    on_hit(hit)
            note_progress(current)
        elif not note_progress(current):
            break
        else:
            time.sleep(POLL_S)

    end = hits[-1].play_at_s + tail_s
    while True:
        current = now()
        if current >= end or not note_progress(current):
            break
        time.sleep(POLL_S)
    return sent
