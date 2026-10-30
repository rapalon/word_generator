"""Unit tests for syllable builder phonological rules."""

import random
from company_name.phonemes import ALLOWED_ONSET_CLUSTERS, PhoneticClass
from company_name.presets import BALANCED_CONFIG
from company_name.syllable_builder import SyllableBuilder


def test_no_forbidden_clusters():
    builder = SyllableBuilder(BALANCED_CONFIG, rng=random.Random(12345))
    allowed = set(ALLOWED_ONSET_CLUSTERS.keys())

    for _ in range(50):
        words = builder.build_word(3)
        for s in words:
            if s.onset and s.onset.is_cluster:
                assert s.onset.symbol in allowed


def test_at_most_one_cluster_per_word():
    builder = SyllableBuilder(BALANCED_CONFIG, rng=random.Random(42))
    for _ in range(100):
        words = builder.build_word(3)
        cluster_count = sum(1 for s in words if s.onset and s.onset.is_cluster)
        assert cluster_count <= 1


def test_no_three_consonants_in_a_row():
    # Never allow coda + onset cluster (which would produce 3 consonants in a row)
    builder = SyllableBuilder(BALANCED_CONFIG, rng=random.Random(999))
    for _ in range(100):
        words = builder.build_word(3)
        for i in range(len(words) - 1):
            if words[i].coda is not None:
                assert words[i + 1].onset is None or not words[i + 1].onset.is_cluster


def test_open_syllables_preference():
    builder = SyllableBuilder(BALANCED_CONFIG, rng=random.Random(777))
    total_syllables = 0
    total_open = 0

    for _ in range(100):
        syls = builder.build_word(builder.choose_syllable_count())
        total_syllables += len(syls)
        total_open += sum(1 for s in syls if s.is_open)

    open_ratio = total_open / total_syllables
    # At least 70% open syllables
    assert open_ratio >= 0.70


def test_memorability_requirement():
    builder = SyllableBuilder(BALANCED_CONFIG, rng=random.Random(314))
    for _ in range(50):
        words = builder.build_word(2)
        all_cons = []
        for s in words:
            if s.onset:
                all_cons.append(s.onset)
            if s.coda:
                all_cons.append(s.coda)

        has_plosive = any(
            c.phonetic_class == PhoneticClass.PLOSIVE or
            (c.is_cluster and any(p in c.symbol for p in "kptbdg"))
            for c in all_cons
        )
        has_sonorant = any(
            c.phonetic_class == PhoneticClass.SONORANT or
            (c.is_cluster and any(r in c.symbol for r in "lmnr"))
            for c in all_cons
        )

        assert has_plosive
        assert has_sonorant
