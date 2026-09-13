"""Phrase and section tracking, fed synthetic bar summaries."""

from tutti.core.listen import BarFeatures
from tutti.core.phrase import PhraseTracker, novelty


def bar(loudness=0.5, density=1.0, register=60.0, pcs=(0, 4, 7), notes=8):
    weights = [0.0] * 12
    for pc in pcs:
        weights[pc % 12] = 1.0 / len(pcs)
    return BarFeatures(loudness=loudness, density=density, register=register,
                       pitch_classes=tuple(weights), notes=notes)


def test_phrases_are_counted_in_fours_with_ends_flagged():
    tracker = PhraseTracker()
    seen = []
    for _ in range(9):
        ctx = tracker.on_bar(bar())
        seen.append((ctx.bar_in_phrase, ctx.phrase_end, ctx.hyper_end))
    assert [s[0] for s in seen] == [1, 2, 3, 0, 1, 2, 3, 0, 1]
    assert [s[1] for s in seen] == [False, False, True, False, False, False, True, False, False]
    assert seen[6][2] and not seen[2][2]      # the period closes at bar 8, not bar 4


def test_ordinary_variation_is_not_a_new_section():
    tracker = PhraseTracker()
    for i in range(16):
        tracker.on_bar(bar(loudness=0.5 + 0.03 * (i % 3), density=1.0 + 0.1 * (i % 2),
                           register=60 + (i % 4), pcs=((0, 4, 7), (5, 9, 0), (7, 11, 2))[i % 3]))
    assert tracker.section == 0


def test_a_real_change_held_for_a_phrase_is_a_section():
    tracker = PhraseTracker()
    for _ in range(8):
        tracker.on_bar(bar())
    # A moderate change: a bit louder, half again as dense, a fifth higher.
    changed = bar(loudness=0.65, density=1.6, register=66)
    for _ in range(3):
        ctx = tracker.on_bar(changed)
        assert ctx.section == 0 and not ctx.section_started      # not yet
    ctx = tracker.on_bar(changed)
    assert ctx.section == 1 and ctx.section_started
    # The section is dated from the first changed bar, so its phrases line up.
    assert ctx.bars_in_section == 4 and ctx.bar_in_phrase == 0
    ctx = tracker.on_bar(changed)
    assert ctx.section == 1 and not ctx.section_started


def test_a_chord_change_is_not_a_section():
    # Two bars on the tonic, two on the subdominant, round and round, at
    # one level: every bar's harmony sits away from the section's blend,
    # and none of it is a section.
    tracker = PhraseTracker()
    for i in range(24):
        pcs = (0, 4, 7) if (i // 2) % 2 == 0 else (5, 9, 0)
        tracker.on_bar(bar(pcs=pcs, register=60 + 4 * ((i // 2) % 2)))
    assert tracker.section == 0


def test_a_lone_new_chord_far_from_the_rest_is_not_extreme():
    tracker = PhraseTracker()
    for _ in range(8):
        tracker.on_bar(bar(pcs=(0, 4, 7)))
    ctx = tracker.on_bar(bar(pcs=(1, 5, 8), register=66))   # a foreign chord, a fifth up
    assert not ctx.section_started


def test_an_extreme_bar_is_a_section_on_its_own():
    tracker = PhraseTracker()
    for _ in range(6):
        tracker.on_bar(bar(loudness=0.3, density=0.8, register=55))
    ctx = tracker.on_bar(bar(loudness=0.9, density=3.0, register=80, pcs=(1, 5, 8)))
    assert ctx.section_started


def test_a_young_section_cannot_end_and_a_lone_odd_bar_is_forgiven():
    tracker = PhraseTracker()
    tracker.on_bar(bar())
    tracker.on_bar(bar(loudness=0.9, density=3.0))     # section is one bar old
    assert tracker.section == 0
    for _ in range(6):
        tracker.on_bar(bar())
    tracker.on_bar(bar(loudness=0.8, density=2.2))     # one odd bar...
    tracker.on_bar(bar())                               # ...then back to normal
    assert tracker.section == 0


def test_rest_bars_are_neutral():
    tracker = PhraseTracker()
    for _ in range(6):
        tracker.on_bar(bar())
    silent = BarFeatures(0.0, 0.0, 0.0, tuple(0.0 for _ in range(12)), notes=0)
    tracker.on_bar(silent)
    tracker.on_bar(silent)
    tracker.on_bar(bar())
    assert tracker.section == 0


def test_novelty_is_zero_for_the_same_bar_and_grows_with_distance():
    same = novelty(bar(), bar())
    louder = novelty(bar(loudness=0.7), bar())
    much_louder = novelty(bar(loudness=0.9), bar())
    assert same == 0.0
    assert 0.0 < louder < much_louder
