"""Converts phonological syllables into orthographic spelling, pronunciation respelling, and IPA."""

from __future__ import annotations

import random
from typing import Sequence

from company_name.phonemes import VowelQuality
from company_name.syllables import Syllable


def render_syllable_spelling(
    syl: Syllable,
    index: int,
    total_syllables: int,
    next_syl: Syllable | None = None,
    rng: random.Random | None = None,
) -> str:
    """Render a single syllable into orthographic spelling based on its context."""
    if rng is None:
        rng = random.Random()

    is_first = (index == 0)
    is_last = (index == total_syllables - 1)

    # 1. Onset rendering
    onset_text = ""
    if syl.onset:
        onset_text = syl.onset.symbol
        # Clarify /k/ spelling:
        # Before 'e', 'i', 'y', 'c' sounds like /s/, so ensure 'k' is used
        target_vowel = syl.nucleus.symbol
        if onset_text == "c" and target_vowel in {"EH", "IH", "IY", "EY"}:
            onset_text = "k"
        elif onset_text == "k" and target_vowel in {"AA", "OW", "UW", "AX"} and not syl.onset.is_cluster:
            # Can be 'c' or 'k'; prefer 'c' slightly for brand softness unless user config
            if rng.random() < 0.4:
                onset_text = "c"

    # 2. Nucleus rendering
    v_key = syl.nucleus.symbol
    vowel_text = ""

    if v_key == "AE":  # /æ/
        vowel_text = "a"
    elif v_key == "EH":  # /ɛ/
        vowel_text = "e"
    elif v_key == "IH":  # /ɪ/
        vowel_text = "i"
    elif v_key == "AA":  # /ɑ/
        # In American English, 'o' is standard for /ɑ/ (as in lot, pot, nov)
        # If followed by 'r', 'a' gives /ɑɹ/ (as in star, car)
        if syl.coda and syl.coda.symbol == "r":
            vowel_text = "a"
        else:
            vowel_text = "o"
    elif v_key == "AH":  # /ʌ/
        vowel_text = "u"
    elif v_key == "IY":  # /i/
        if is_last:
            # End of word: brand names love -i or -y, occasionally -ee
            vowel_text = rng.choice(["i", "y", "a", "ee"] if not syl.coda else ["ee"])
            if vowel_text == "a":  # If picked 'a', keep vowel as /ə/
                vowel_text = "i"
        elif syl.is_open:
            # Open non-final syllable: 'i' (as in Marina, Alina) or 'ee'
            vowel_text = "i" if (next_syl and next_syl.onset) else "ee"
        else:
            vowel_text = "ee"
    elif v_key == "EY":  # /eɪ/
        if is_last and syl.is_open:
            vowel_text = "ay"
        elif syl.is_open:
            vowel_text = "a"
        else:
            vowel_text = "ai"
    elif v_key == "OW":  # /oʊ/
        vowel_text = "o"
    elif v_key == "UW":  # /u/
        if syl.is_open:
            vowel_text = "u"
        else:
            vowel_text = "oo"
    elif v_key == "AX":  # /ə/ (schwa)
        if is_last:
            vowel_text = "a"
        else:
            vowel_text = "a" if rng.random() < 0.6 else "e"
    else:
        vowel_text = "a"

    # 3. Coda rendering
    coda_text = ""
    if syl.coda:
        coda_text = syl.coda.symbol

    return f"{onset_text}{vowel_text}{coda_text}"


def render_syllables_to_spelling(
    syllables: Sequence[Syllable],
    rng: random.Random | None = None,
) -> tuple[str, str]:
    """Render syllables to (CapitalizedSpelling, dot_separated_syllables)."""
    if rng is None:
        rng = random.Random()

    n = len(syllables)
    rendered_parts: list[str] = []

    for i, syl in enumerate(syllables):
        nxt = syllables[i + 1] if i + 1 < n else None
        part = render_syllable_spelling(syl, i, n, next_syl=nxt, rng=rng)
        rendered_parts.append(part.lower())

    dot_breakdown = ".".join(rendered_parts)
    full_spelling = "".join(rendered_parts).capitalize()
    return full_spelling, dot_breakdown


def render_syllable_respelling(syl: Syllable, is_last: bool) -> str:
    """Render a single syllable into phonetic respelling notation."""
    onset = syl.onset.respelling if syl.onset else ""
    coda = syl.coda.respelling if syl.coda else ""
    has_r_coda = (syl.coda is not None and syl.coda.symbol == "r")

    v_key = syl.nucleus.symbol
    if syl.is_stressed:
        vowel_map = {
            "AE": "A",
            "EH": "EH",
            "IH": "IH",
            "AA": "AR" if has_r_coda else "AH",
            "AH": "UH",
            "IY": "EE",
            "EY": "AY",
            "OW": "OR" if has_r_coda else "OH",
            "UW": "OO",
            "AX": "UH",
        }
        v_str = vowel_map.get(v_key, "AH")
        # If r was handled in the vowel symbol (AR, OR), don't duplicate coda
        c_str = "" if (has_r_coda and v_key in {"AA", "OW"}) else coda
        return f"{onset}{v_str}{c_str}".upper()
    else:
        vowel_map = {
            "AE": "a",
            "EH": "eh",
            "IH": "ih",
            "AA": "ar" if has_r_coda else "ah",
            "AH": "uh",
            "IY": "ee",
            "EY": "ay",
            "OW": "or" if has_r_coda else "oh",
            "UW": "oo",
            "AX": "uh",
        }
        v_str = vowel_map.get(v_key, "uh")
        c_str = "" if (has_r_coda and v_key in {"AA", "OW"}) else coda
        return f"{onset}{v_str}{c_str}".lower()


def render_word_respelling(syllables: Sequence[Syllable]) -> str:
    """Render full word respelling with stressed syllable in uppercase.

    Example: 'loo-MOR-uh', 'MAR-loh'
    """
    n = len(syllables)
    parts: list[str] = []

    # Handle intervocalic r transition: if syl[i] is stressed OW or AA (open) and syl[i+1] has onset 'r'
    i = 0
    while i < n:
        syl = syllables[i]
        nxt = syllables[i + 1] if i + 1 < n else None

        if nxt and nxt.onset and nxt.onset.symbol == "r" and syl.is_open and syl.nucleus.symbol in {"OW", "AA"}:
            onset_str = syl.onset.respelling if syl.onset else ""
            if syl.is_stressed:
                v_str = "OR" if syl.nucleus.symbol == "OW" else "AR"
                parts.append(f"{onset_str}{v_str}".upper())
            else:
                v_str = "or" if syl.nucleus.symbol == "OW" else "ar"
                parts.append(f"{onset_str}{v_str}".lower())

            # For next syllable, drop the 'r' in respelling since it merged with previous syllable
            nxt_onset_str = ""
            nxt_coda_str = nxt.coda.respelling if nxt.coda else ""
            v_key = nxt.nucleus.symbol
            if nxt.is_stressed:
                nxt_v = "UH" if v_key == "AX" else nxt.nucleus.stressed_respelling
                parts.append(f"{nxt_onset_str}{nxt_v}{nxt_coda_str}".upper())
            else:
                nxt_v = "uh" if v_key == "AX" else nxt.nucleus.unstressed_respelling
                parts.append(f"{nxt_onset_str}{nxt_v}{nxt_coda_str}".lower())
            i += 2
            continue

        parts.append(render_syllable_respelling(syl, is_last=(i == n - 1)))
        i += 1

    return "-".join(parts)


def render_word_ipa(syllables: Sequence[Syllable]) -> str:
    """Render full word in standard American English IPA with primary stress mark ˈ."""
    parts: list[str] = []
    n = len(syllables)

    for i, syl in enumerate(syllables):
        nxt = syllables[i + 1] if i + 1 < n else None

        if syl.is_stressed:
            parts.append("ˈ")
        if syl.onset:
            parts.append(syl.onset.ipa)

        # Contextual allophone for vowel:
        # e.g., /oʊ/ followed by /ɹ/ merges to /ɔɹ/ (as in Lumora /luˈmɔɹə/)
        has_r_next = (syl.coda and syl.coda.symbol == "r") or (nxt and nxt.onset and nxt.onset.symbol == "r")
        if syl.nucleus.symbol == "OW" and has_r_next:
            parts.append("ɔ")
        else:
            parts.append(syl.nucleus.ipa)

        if syl.coda:
            parts.append(syl.coda.ipa)

    return f"/{''.join(parts)}/"
