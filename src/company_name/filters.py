"""Candidate word filtering for real words, profanities, slurs, and awkward letter sequences."""

from __future__ import annotations

import gzip
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional, Set

from company_name.syllables import Syllable

DATA_DIR = Path(__file__).parent / "data"
ENGLISH_WORDS_GZ = DATA_DIR / "english_words.txt.gz"

# List of offensive terms, slurs, vulgarities, and sensitive words to block
PROFANITY_BLOCKLIST = {
    # Common vulgarities / sexual
    "fuck", "shit", "bitch", "cunt", "cock", "dick", "pussy", "tits", "titties",
    "boob", "boobs", "penis", "vagina", "clit", "twat", "wank", "wanker", "piss",
    "ass", "asshole", "arse", "bastard", "dammit", "slut", "whore", "dildo",
    "jizz", "cum", "semen", "sperm", "boner", "shat", "prick", "skank", "fag",
    "faggot", "dyke", "homo", "queer", "tranny", "retard", "spic", "chink",
    "gook", "kike", "nigger", "nigga", "coon", "wetback", "raghead", "towelhead",
    "nazi", "hitler", "kkk", "rape", "rapist", "pedophile", "pedo", "incest",
    "scat", "porn", "fetish", "anus", "rectum", "orgasm",
    # Substring variants and common compound terms
    "fuk", "shyt", "btch", "cnt", "dik", "dck", "pusy", "fck", "fux", "azz",
}


@lru_cache(maxsize=1)
def load_english_wordlist() -> Set[str]:
    """Load the bundled set of English words."""
    words: set[str] = set()
    if ENGLISH_WORDS_GZ.exists():
        with gzip.open(ENGLISH_WORDS_GZ, "rt", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    words.add(w)
    return words


def normalize_leetspeak(text: str) -> str:
    """Normalize common leetspeak substitutions to plain letters."""
    substitutions = {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "8": "b",
        "@": "a",
        "$": "s",
    }
    lowered = text.lower()
    for char, replacement in substitutions.items():
        lowered = lowered.replace(char, replacement)
    return lowered


def contains_profanity_or_slur(word: str) -> bool:
    """Check if word contains or closely matches profanity or slurs."""
    normalized = normalize_leetspeak(word.lower())

    # Check direct match and substring match
    for bad in PROFANITY_BLOCKLIST:
        if bad in normalized:
            return True

    # Check with duplicate adjacent letters collapsed (e.g. "shiiit" -> "shit")
    collapsed = re.sub(r"(.)\1+", r"\1", normalized)
    for bad in PROFANITY_BLOCKLIST:
        if bad in collapsed:
            return True

    return False


def has_awkward_letter_sequences(
    spelling: str,
    syllables: Optional[list[Syllable]] = None,
    allow_reduplication: bool = False,
) -> bool:
    """Check for awkward or ambiguous letter sequences:

    - Doubled vowels other than 'ee' / 'oo' (e.g., 'aa', 'ii', 'uu', 'yy')
    - 'wh' mid-word
    - Three or more consonants in a row
    - Repeated back-to-back syllables (reduplication)
    - Ambiguous spellings like initial 'x', trailing solitary 'c', or 'c' followed by 'e'/'i'
    """
    s = spelling.lower()

    # Doubled vowels check: only 'ee' and 'oo' are allowed
    vowel_doubles = re.findall(r"([aeiouy])\1", s)
    for vd in vowel_doubles:
        if vd not in {"e", "o"}:
            return True

    # Specific forbidden double vowels: 'yy', 'ii', 'uu', 'aa'
    if any(double in s for double in ("yy", "ii", "uu", "aa")):
        return True

    # 'wh' anywhere except strictly at the start
    if re.search(r".wh", s):
        return True

    # 3 or more consecutive consonants (e.g., 'str' is onset cluster, but no 3 consonants in a row)
    if re.search(r"[bcdfghjklmnpqrstvwxz]{3,}", s):
        return True

    # Ambiguous spellings:
    # 1. Trailing 'c' without 'k' (e.g. 'Novac' vs 'Novak')
    if s.endswith("c"):
        return True

    # 2. 'x' at start of word (sounds like /z/ or /ks/, confusing to English speakers)
    if s.startswith("x"):
        return True

    # 3. Soft 'c' confusion: 'c' followed by 'e', 'i', or 'y' might be read as /s/ or /k/
    if re.search(r"c[eiy]", s):
        return True

    # 4. Immediate syllable reduplication (e.g. 'mimi', 'koko', 'lulun')
    if not allow_reduplication and syllables:
        rendered_syls = [s.to_respelling().lower() for s in syllables]
        for i in range(len(rendered_syls) - 1):
            if rendered_syls[i] == rendered_syls[i + 1]:
                return True

    return False


class WordFilter:
    """Combines all phonological and orthographic rejection filters."""

    def __init__(
        self,
        allow_real_words: bool = False,
        allow_reduplication: bool = False,
        min_length: int = 4,
        max_length: int = 9,
    ) -> None:
        self.allow_real_words = allow_real_words
        self.allow_reduplication = allow_reduplication
        self.min_length = min_length
        self.max_length = max_length
        self._english_words = load_english_wordlist()

    def is_valid(self, spelling: str, syllables: Optional[list[Syllable]] = None) -> tuple[bool, str]:
        """Validate candidate word. Returns (is_valid, reason_if_invalid)."""
        clean_word = spelling.strip()
        lower_word = clean_word.lower()

        # Length check
        if not (self.min_length <= len(clean_word) <= self.max_length):
            return False, f"Length {len(clean_word)} outside range [{self.min_length}, {self.max_length}]"

        # Real English word check
        if not self.allow_real_words and lower_word in self._english_words:
            return False, f"Real English word: {lower_word}"

        # Profanity or slur check
        if contains_profanity_or_slur(lower_word):
            return False, "Contains profanity or offensive substring"

        # Letter sequence check
        if has_awkward_letter_sequences(
            lower_word,
            syllables=syllables,
            allow_reduplication=self.allow_reduplication,
        ):
            return False, "Contains awkward or ambiguous letter sequences"

        return True, ""
