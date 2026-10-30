"""Unit tests for spelling, respelling, and IPA mapping."""

from company_name.phonemes import CONSONANTS, VOWELS
from company_name.spelling_mapper import (
    render_syllables_to_spelling,
    render_word_ipa,
    render_word_respelling,
)
from company_name.syllables import Syllable


def test_spelling_and_representations_example():
    # Test Lumora representation: lu.mo.ra
    s1 = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["UW"], is_stressed=False)
    s2 = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["OW"], is_stressed=True)
    s3 = Syllable(onset=CONSONANTS["r"], nucleus=VOWELS["AX"], is_stressed=False)

    spelling, breakdown = render_syllables_to_spelling([s1, s2, s3])
    respelling = render_word_respelling([s1, s2, s3])
    ipa = render_word_ipa([s1, s2, s3])

    assert spelling == "Lumora"
    assert breakdown == "lu.mo.ra"
    assert respelling == "loo-MOR-uh"
    assert ipa == "/luˈmɔɹə/"


def test_stress_caps_in_respelling():
    # First syllable stressed
    s1 = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["AA"], coda=CONSONANTS["r"], is_stressed=True)
    s2 = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["OW"], is_stressed=False)

    respelling = render_word_respelling([s1, s2])
    assert respelling.startswith("MAR-")
    assert respelling.endswith("-loh")


def test_k_not_c_before_front_vowels():
    # Before front vowels (EH, IH, IY, EY), onset /k/ should be spelled 'k', never 'c'
    syl = Syllable(onset=CONSONANTS["k"], nucleus=VOWELS["EH"])
    spelling, _ = render_syllables_to_spelling([syl])
    assert spelling.lower().startswith("k")
