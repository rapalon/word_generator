"""Stress assignment and vowel reduction rules for American English."""

from __future__ import annotations

from company_name.phonemes import VOWELS, VowelQuality
from company_name.syllables import Syllable


def assign_stress_and_reduction(syllables: list[Syllable]) -> list[Syllable]:
    """Assign stress pattern and apply appropriate unstressed vowel reduction.

    Rules:
    - 1 syllable: primary stress on the only syllable.
    - 2 syllables: trochaic (first syllable stressed, e.g., 'MAR-lo').
    - 3 syllables: first syllable stressed by default; penultimate stress when
      middle syllable is heavy (closed or long/tense vowel, e.g., 'ka-NO-la', 'ma-RI-na').
    - 4 syllables: primary stress on second syllable if heavy, else first syllable.
    """
    n = len(syllables)
    if n == 0:
        return syllables

    # Reset all stress marks
    for syl in syllables:
        syl.is_stressed = False

    if n == 1:
        syllables[0].is_stressed = True
    elif n == 2:
        # Trochaic stress: 1st syllable
        syllables[0].is_stressed = True
    elif n == 3:
        # Check if middle syllable is heavy
        middle_is_heavy = syllables[1].is_heavy
        if middle_is_heavy:
            syllables[1].is_stressed = True
        else:
            syllables[0].is_stressed = True
    else:  # 4 or more syllables
        if syllables[1].is_heavy:
            syllables[1].is_stressed = True
        else:
            syllables[0].is_stressed = True

    # Apply vowel reduction to schwa /ə/ for unstressed vowels where natural
    # Especially:
    # 1. Unstressed lax vowels (/ʌ/, /æ/) reduce to schwa /ə/
    # 2. Final open unstressed syllable ending in /ɑ/ or /æ/ reduces to schwa /ə/ (spelled 'a')
    # Note: tense vowels like final /oʊ/ (Marlo), final /i/ (Lumi) stay tense.
    for i, syl in enumerate(syllables):
        if not syl.is_stressed:
            v_key = syl.nucleus.symbol
            # If final unstressed open syllable with lax vowel or AA, it becomes schwa (rendered as 'a' or 'uh')
            if i == n - 1 and syl.is_open:
                if v_key in {"AA", "AH", "AE", "EH"}:
                    syl.nucleus = VOWELS["AX"]
            elif syl.is_open and v_key in {"AH", "AE"}:
                syl.nucleus = VOWELS["AX"]

    return syllables
