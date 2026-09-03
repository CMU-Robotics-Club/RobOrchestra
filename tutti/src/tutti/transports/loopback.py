"""Play a plan through the speakers instead of through robots.

This exists so that nobody needs to be in the Roboclub room with a working MIDI
chain to work on Tutti. It is also the reference against which the real
transports get judged: the mixer places every hit on an exact sample, so
anything you hear that is not tight is the plan's fault, not the link's.

The mixer is deliberately free of any audio library so it can be tested in CI,
where there is no sound card. LoopbackTransport is the thin part that needs one.
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Iterable

import numpy as np

from ..core.plan import Instrument, ScheduledHit
from . import synth
from .base import Transport

DEFAULT_SAMPLE_RATE = 48_000
DEFAULT_BLOCK = 256


class Mixer:
    """Sums scheduled hits into blocks of audio.

    Time is counted in frames since the stream started, so a hit landing part
    way through a block lands part way through that block rather than being
    rounded to its edge. Getting this right is the whole reason loopback is
    worth trusting as a reference.
    """

    def __init__(self, sample_rate: int = DEFAULT_SAMPLE_RATE,
                 roles: dict[str, str] | None = None, master_gain: float = 0.35):
        self.sample_rate = sample_rate
        self.master_gain = master_gain
        self._roles = roles or {}
        self._cache: dict[tuple[str, int], np.ndarray] = {}
        self._voices: list[tuple[int, np.ndarray, float]] = []
        self._frame = 0
        self.clipped_blocks = 0

    @property
    def frame(self) -> int:
        return self._frame

    @property
    def now_s(self) -> float:
        return self._frame / self.sample_rate

    def sample_for(self, bot_id: str, note: int) -> np.ndarray:
        role = self._roles.get(bot_id, "")
        key = (role, note)
        if key not in self._cache:
            self._cache[key] = synth.for_role(role, note, self.sample_rate)
        return self._cache[key]

    def schedule(self, hit: ScheduledHit) -> None:
        start = int(round(hit.play_at_s * self.sample_rate))
        gain = max(hit.velocity, 1) / 127.0
        self._voices.append((start, self.sample_for(hit.bot_id, hit.note), gain))

    def render(self, frames: int) -> np.ndarray:
        out = np.zeros(frames, dtype=np.float32)
        block_start = self._frame
        block_end = block_start + frames

        still_live = []
        for voice in self._voices:
            start, wave, gain = voice
            end = start + wave.size
            if end > block_end:
                still_live.append(voice)    # still has audio after this block
            if start >= block_end or end <= block_start:
                continue                    # not started, or already finished
            lo = max(start, block_start)
            hi = min(end, block_end)
            out[lo - block_start:hi - block_start] += wave[lo - start:hi - start] * gain

        self._voices = still_live
        self._frame = block_end

        out *= self.master_gain
        if np.max(np.abs(out)) > 1.0:
            # Usually means more voices landed together than the real bots could
            # sustain, so it is worth counting rather than silently squashing.
            self.clipped_blocks += 1
            np.clip(out, -1.0, 1.0, out=out)
        return out

    @property
    def pending(self) -> int:
        return len(self._voices)


class LoopbackTransport(Transport):
    """Renders a plan to the default audio output."""

    name = "loopback"

    def __init__(self, instruments: dict[str, Instrument] | None = None,
                 sample_rate: int = DEFAULT_SAMPLE_RATE, block: int = DEFAULT_BLOCK,
                 master_gain: float = 0.35):
        roles = {bot_id: inst.role for bot_id, inst in (instruments or {}).items()}
        self.mixer = Mixer(sample_rate, roles, master_gain)
        self._block = block
        self._stream = None
        self._incoming: queue.SimpleQueue[ScheduledHit] = queue.SimpleQueue()
        self._sent = 0
        self._lock = threading.Lock()

    @property
    def lookahead_s(self) -> float:
        # In process, so all that is needed is a couple of audio blocks.
        return 4.0 * self._block / self.mixer.sample_rate

    @property
    def now_s(self) -> float:
        return self.mixer.now_s

    def start(self) -> None:
        if self._stream is not None:
            return
        try:
            import sounddevice as sd
        except Exception as exc:
            raise RuntimeError(
                "loopback needs sounddevice: uv sync --extra audio"
            ) from exc

        self._stream = sd.OutputStream(
            samplerate=self.mixer.sample_rate,
            channels=1,
            blocksize=self._block,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, outdata, frames, time_info, status) -> None:
        # Runs on the audio thread. Drain whatever the player handed over, then
        # render. Keep this short; anything slow here is an audible dropout.
        while True:
            try:
                self.mixer.schedule(self._incoming.get_nowait())
            except queue.Empty:
                break
        outdata[:, 0] = self.mixer.render(frames)

    def send(self, hits: Iterable[ScheduledHit]) -> int:
        n = 0
        for hit in hits:
            self._incoming.put(hit)
            n += 1
        with self._lock:
            self._sent += n
        return n

    @property
    def sent(self) -> int:
        with self._lock:
            return self._sent

    def close(self) -> None:
        if self._stream is None:
            return
        self._stream.stop()
        self._stream.close()
        self._stream = None


def render_to_wav(hits, path, instruments=None, sample_rate: int = DEFAULT_SAMPLE_RATE,
                  master_gain: float = 0.35, tail_s: float = 1.0) -> float:
    """Render hits to a mono 16-bit WAV. Returns the duration written.

    Needs no sound card, which makes it the way to hear a change on a machine
    with no working audio, and the way to check output in CI. Uses the stdlib
    wave module so it adds no dependency.
    """
    import wave as wave_mod

    hits = sorted(hits, key=lambda h: h.play_at_s)
    if not hits:
        raise ValueError("nothing to render")

    roles = {bot_id: inst.role for bot_id, inst in (instruments or {}).items()}
    mixer = Mixer(sample_rate, roles, master_gain)
    for hit in hits:
        mixer.schedule(hit)

    total = int((hits[-1].play_at_s + tail_s) * sample_rate)
    blocks = []
    rendered = 0
    while rendered < total:
        n = min(DEFAULT_BLOCK, total - rendered)
        blocks.append(mixer.render(n))
        rendered += n

    audio = np.concatenate(blocks) if blocks else np.zeros(0, dtype=np.float32)
    pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")

    with wave_mod.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sample_rate)
        out.writeframes(pcm.tobytes())
    return audio.size / sample_rate


class NullTransport(Transport):
    """Accepts everything and does nothing. For dry runs and tests."""

    name = "null"

    def __init__(self):
        self.received: list[ScheduledHit] = []

    def send(self, hits: Iterable[ScheduledHit]) -> int:
        before = len(self.received)
        self.received.extend(hits)
        return len(self.received) - before
