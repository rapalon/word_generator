"""Unit tests for stress assignment and vowel reduction."""

from company_name.phonemes import CONSONANTS, VOWELS, VowelQuality
from company_name.stress import assign_stress_and_reduction
from company_name.syllables import Syllable


def test_one_syllable_stress():
    syl = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["UW"])
    words = assign_stress_and_reduction([syl])
    assert len(words) == 1
    assert words[0].is_stressed


def test_two_syllable_trochaic_stress():
    # 2 syllables must have stress on first syllable (trochaic, e.g. MAR-lo)
    for _ in range(10):
        s1 = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["AA"], coda=CONSONANTS["r"])
        s2 = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["OW"])
        words = assign_stress_and_reduction([s1, s2])
        assert words[0].is_stressed
        assert not words[1].is_stressed


def test_three_syllable_default_and_heavy_middle():
    # Default 3 syllables with light middle: initial stress
    s1 = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["UW"])
    s2 = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["EH"])  # light (open lax)
    s3 = Syllable(onset=CONSONANTS["r"], nucleus=VOWELS["AA"])
    res = assign_stress_and_reduction([s1, s2, s3])
    assert res[0].is_stressed
    assert not res[1].is_stressed

    # 3 syllables with heavy middle (closed): penultimate stress (e.g., Kal-vin-a / ka-NO-la)
    s1 = Syllable(onset=CONSONANTS["k"], nucleus=VOWELS["AE"])
    s2 = Syllable(onset=CONSONANTS["n"], nucleus=VOWELS["OW"])  # tense vowel = heavy
    s3 = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["AX"])
    res2 = assign_stress_and_reduction([s1, s2, s3])
    assert not res2[0].is_stressed
    assert res2[1].is_stressed  # penultimate stress
    assert not res2[2].is_stressed

    # 3 syllables with closed middle (CVC = heavy)
    s1_c = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["AE"])
    s2_c = Syllable(onset=CONSONANTS["r"], nucleus=VOWELS["IH"], coda=CONSONANTS["n"]) # closed
    s3_c = Syllable(onset=CONSONANTS["t"], nucleus=VOWELS["AX"])
    res3 = assign_stress_and_reduction([s1_c, s2_c, s3_c])
    assert res3[1].is_stressed


def test_unstressed_reduction_to_schwa():
    # Final unstressed open syllable with lax vowel or AA reduces to schwa /ə/
    s1 = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["UW"])
    s2 = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["OW"], coda=CONSONANTS["r"])
    s3 = Syllable(onset=None, nucleus=VOWELS["AA"])  # final unstressed open
    res = assign_stress_and_reduction([s1, s2, s3])
    assert res[2].nucleus.quality == VowelQuality.SCHWA
    assert res[2].nucleus.ipa == "ə"
