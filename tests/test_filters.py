"""Unit tests for word rejection filters."""

from company_name.filters import WordFilter, contains_profanity_or_slur, has_awkward_letter_sequences
from company_name.phonemes import CONSONANTS, VOWELS
from company_name.syllables import Syllable


def test_reject_real_english_words():
    wf_strict = WordFilter(allow_real_words=False)
    wf_allow = WordFilter(allow_real_words=True)

    # Common English words matching syllable and letter structure
    for real_word in ["water", "planet", "table", "river", "melon", "lemon"]:
        valid_strict, reason = wf_strict.is_valid(real_word)
        assert not valid_strict
        assert "Real English word" in reason

        valid_allow, _ = wf_allow.is_valid(real_word)
        assert valid_allow


def test_profanity_and_slurs_filter():
    assert contains_profanity_or_slur("fuck")
    assert contains_profanity_or_slur("shiiit")
    assert contains_profanity_or_slur("b1tch")  # leetspeak
    assert contains_profanity_or_slur("nazi")
    assert contains_profanity_or_slur("asshole")

    assert not contains_profanity_or_slur("Lumora")
    assert not contains_profanity_or_slur("Velo")
    assert not contains_profanity_or_slur("Marlo")


def test_awkward_letter_sequences():
    # Doubled vowels other than ee / oo
    assert has_awkward_letter_sequences("Taalon")   # aa
    assert has_awkward_letter_sequences("Tiina")    # ii
    assert has_awkward_letter_sequences("Tuula")    # uu
    assert has_awkward_letter_sequences("Tyyla")    # yy

    # Allowed doubled vowels
    assert not has_awkward_letter_sequences("Teena")  # ee
    assert not has_awkward_letter_sequences("Toona")  # oo

    # wh mid-word
    assert has_awkward_letter_sequences("Awhin")
    assert not has_awkward_letter_sequences("White")

    # Three consonants in a row
    assert has_awkward_letter_sequences("Kalbrin")


def test_length_limits():
    wf = WordFilter(min_length=4, max_length=9)

    # Too short (< 4)
    v, _ = wf.is_valid("Cat")
    assert not v

    # Too long (> 9)
    v, _ = wf.is_valid("Supercalifrag")
    assert not v

    # Allowed length (4 - 9)
    v, _ = wf.is_valid("Lumora")
    assert v


def test_reduplication_filter():
    s1 = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["IY"])
    s2 = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["IY"])

    wf_no_redup = WordFilter(allow_real_words=True, allow_reduplication=False)
    wf_allow_redup = WordFilter(allow_real_words=True, allow_reduplication=True)

    v1, _ = wf_no_redup.is_valid("Mimi", syllables=[s1, s2])
    assert not v1

    v2, _ = wf_allow_redup.is_valid("Mimi", syllables=[s1, s2])
    assert v2
