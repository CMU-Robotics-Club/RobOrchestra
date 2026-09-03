"""The latency probe's analysis, on synthesised drum recordings."""

import numpy as np
import pytest

from tutti.core.latency import LatencyReport, detect_onsets, match_hits
from tutti.transports import synth

SR = 48_000


def recording(hit_times, seconds=4.0, noise=0.0005, seed=0):
    rng = np.random.default_rng(seed)
    audio = rng.normal(0.0, noise, int(seconds * SR)).astype(np.float32)
    voice = synth.snare(SR)
    for t in hit_times:
        start = int(round(t * SR))
        end = min(start + voice.size, audio.size)
        audio[start:end] += 0.6 * voice[: end - start]
    return audio


def test_onsets_are_found_where_the_hits_were_placed():
    hits = [0.5, 1.25, 2.0, 2.75]
    found = detect_onsets(recording(hits), SR)
    assert len(found) == len(hits)
    for want, got in zip(hits, found):
        assert abs(got - want) < 0.002, f"onset at {got:.4f}, hit at {want:.4f}"


def test_a_hit_rings_as_one_onset_not_several():
    found = detect_onsets(recording([1.0]), SR)
    assert len(found) == 1


def test_silence_has_no_onsets():
    found = detect_onsets(recording([]), SR)
    assert found == []


def test_matching_reports_latency_missed_and_spurious():
    intended = [0.5, 1.25, 2.0, 2.75]
    # The bot lands each hit 40 ms late, misses the third, and something
    # else in the room bangs at 3.4 s.
    onsets = [0.54, 1.29, 2.79, 3.4]
    report = match_hits(intended, onsets)
    assert report.intended == 4
    assert report.matched == 3
    assert report.missed == 1
    assert report.spurious == 1
    assert report.median_ms == pytest.approx(40.0, abs=1e-6)
    assert report.usable
    assert report.suggested_mech_latency_ms(22.0) == pytest.approx(62.0)


def test_an_onset_slightly_early_still_counts():
    report = match_hits([1.0], [0.99])
    assert report.matched == 1
    assert report.median_ms == pytest.approx(-10.0)


def test_end_to_end_on_a_clean_recording_reads_near_zero():
    hits = [0.5 + 0.75 * k for k in range(6)]
    found = detect_onsets(recording(hits, seconds=6.0), SR)
    report = match_hits(hits, found)
    assert report.matched == 6 and report.missed == 0 and report.spurious == 0
    assert abs(report.median_ms) < 2.0
    assert report.stdev_ms < 1.0


def test_signal_quality_is_measured_and_gates_belief():
    from tutti.core.latency import signal_stats

    peak, snr = signal_stats(recording([0.5, 1.5]))
    assert peak > 0.3
    assert snr > 40.0
    quiet_peak, quiet_snr = signal_stats(recording([], noise=0.0005))
    assert quiet_snr < 15.0
    believable = match_hits([0.5], [0.52], peak=peak, snr_db=snr)
    assert believable.clean
    doubtful = match_hits([0.5], [0.52], peak=0.02, snr_db=10.0)
    assert not doubtful.clean


def test_too_few_matches_is_not_usable():
    report = LatencyReport(intended=10, samples_ms=(20.0, 21.0), missed=8, spurious=0)
    assert not report.usable
    assert np.isnan(LatencyReport(intended=3, samples_ms=(), missed=3, spurious=0).median_ms)
