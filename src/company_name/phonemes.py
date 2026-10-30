"""Phoneme inventories, phonetic categories, and data structures for American English euphony."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PhoneticClass(str, Enum):
    SONORANT = "sonorant"      # l, m, n, r
    PLOSIVE = "plosive"        # k, t, p, b, d, g
    FRICATIVE = "fricative"    # s, v, f, z, h
    APPROXIMANT = "approximant"# y, w
    CLUSTER = "cluster"        # bl, br, cl, etc.


class VowelQuality(str, Enum):
    SHORT_LAX = "short_lax"    # /æ/, /ɛ/, /ɪ/, /ɑ/, /ʌ/
    LONG_TENSE = "long_tense"  # /i/, /eɪ/, /oʊ/, /u/
    SCHWA = "schwa"            # /ə/


class VowelPosition(str, Enum):
    FRONT = "front"            # /i/, /eɪ/, /ɛ/, /æ/, /ɪ/
    CENTRAL = "central"        # /ə/, /ʌ/
    BACK = "back"              # /u/, /oʊ/, /ɑ/


@dataclass(frozen=True)
class Consonant:
    symbol: str
    phonetic_class: PhoneticClass
    ipa: str
    respelling: str
    can_onset: bool = True
    can_coda: bool = True
    is_cluster: bool = False
    default_weight: float = 1.0


@dataclass(frozen=True)
class Vowel:
    symbol: str               # e.g., "AE", "IY", "OW", "AX"
    quality: VowelQuality
    position: VowelPosition
    ipa: str
    stressed_respelling: str   # e.g., "EE", "AY", "OH"
    unstressed_respelling: str # e.g., "ee", "ay", "oh"
    default_weight: float = 1.0


# ---------------------------------------------------------------------------
# Consonant Inventory
# ---------------------------------------------------------------------------

CONSONANTS: dict[str, Consonant] = {
    # High weight - soft and melodic sonorants
    "l": Consonant("l", PhoneticClass.SONORANT, "l", "l", default_weight=3.5),
    "m": Consonant("m", PhoneticClass.SONORANT, "m", "m", default_weight=3.2),
    "n": Consonant("n", PhoneticClass.SONORANT, "n", "n", default_weight=3.2),
    "r": Consonant("r", PhoneticClass.SONORANT, "ɹ", "r", default_weight=3.0),

    # Medium weight
    "s": Consonant("s", PhoneticClass.FRICATIVE, "s", "s", default_weight=2.2),
    "v": Consonant("v", PhoneticClass.FRICATIVE, "v", "v", default_weight=2.0),
    "d": Consonant("d", PhoneticClass.PLOSIVE, "d", "d", default_weight=2.0),
    "b": Consonant("b", PhoneticClass.PLOSIVE, "b", "b", default_weight=2.0),
    "k": Consonant("k", PhoneticClass.PLOSIVE, "k", "k", default_weight=2.0),
    "t": Consonant("t", PhoneticClass.PLOSIVE, "t", "t", default_weight=2.0),

    # Lower weight
    "p": Consonant("p", PhoneticClass.PLOSIVE, "p", "p", default_weight=1.2),
    "g": Consonant("g", PhoneticClass.PLOSIVE, "ɡ", "g", default_weight=1.1),
    "f": Consonant("f", PhoneticClass.FRICATIVE, "f", "f", default_weight=1.1),
    "z": Consonant("z", PhoneticClass.FRICATIVE, "z", "z", default_weight=0.9),
    "h": Consonant("h", PhoneticClass.FRICATIVE, "h", "h", can_coda=False, default_weight=0.9),
    "y": Consonant("y", PhoneticClass.APPROXIMANT, "j", "y", can_coda=False, default_weight=0.9),
    "w": Consonant("w", PhoneticClass.APPROXIMANT, "w", "w", can_coda=False, default_weight=0.8),

    # Rare final consonant
    "x": Consonant("x", PhoneticClass.FRICATIVE, "ks", "x", can_onset=False, can_coda=True, default_weight=0.1),
}

# Whitelist of allowed onset consonant clusters
ALLOWED_ONSET_CLUSTERS: dict[str, Consonant] = {
    "bl": Consonant("bl", PhoneticClass.CLUSTER, "bl", "bl", can_coda=False, is_cluster=True, default_weight=1.0),
    "br": Consonant("br", PhoneticClass.CLUSTER, "bɹ", "br", can_coda=False, is_cluster=True, default_weight=1.0),
    "cl": Consonant("cl", PhoneticClass.CLUSTER, "kl", "kl", can_coda=False, is_cluster=True, default_weight=0.9),
    "cr": Consonant("cr", PhoneticClass.CLUSTER, "kɹ", "kr", can_coda=False, is_cluster=True, default_weight=0.9),
    "dr": Consonant("dr", PhoneticClass.CLUSTER, "dɹ", "dr", can_coda=False, is_cluster=True, default_weight=0.9),
    "fl": Consonant("fl", PhoneticClass.CLUSTER, "fl", "fl", can_coda=False, is_cluster=True, default_weight=0.9),
    "fr": Consonant("fr", PhoneticClass.CLUSTER, "fɹ", "fr", can_coda=False, is_cluster=True, default_weight=0.9),
    "gl": Consonant("gl", PhoneticClass.CLUSTER, "ɡl", "gl", can_coda=False, is_cluster=True, default_weight=0.8),
    "gr": Consonant("gr", PhoneticClass.CLUSTER, "ɡɹ", "gr", can_coda=False, is_cluster=True, default_weight=0.8),
    "pl": Consonant("pl", PhoneticClass.CLUSTER, "pl", "pl", can_coda=False, is_cluster=True, default_weight=1.0),
    "pr": Consonant("pr", PhoneticClass.CLUSTER, "pɹ", "pr", can_coda=False, is_cluster=True, default_weight=1.0),
    "tr": Consonant("tr", PhoneticClass.CLUSTER, "tɹ", "tr", can_coda=False, is_cluster=True, default_weight=0.9),
    "st": Consonant("st", PhoneticClass.CLUSTER, "st", "st", can_coda=False, is_cluster=True, default_weight=0.8),
    "sl": Consonant("sl", PhoneticClass.CLUSTER, "sl", "sl", can_coda=False, is_cluster=True, default_weight=0.8),
}

# Codas: allowed single consonants in coda position
# Primarily sonorants (l, m, n, r) and clean stops/fricatives (s, t, d, k, p, x rare)
ALLOWED_CODAS: dict[str, Consonant] = {
    k: c for k, c in CONSONANTS.items() if c.can_coda and k not in {"h", "y", "w"}
}


# ---------------------------------------------------------------------------
# Vowel Inventory
# ---------------------------------------------------------------------------

VOWELS: dict[str, Vowel] = {
    # Short / lax vowels (mostly in closed or unstressed syllables)
    "AE": Vowel("AE", VowelQuality.SHORT_LAX, VowelPosition.FRONT, "æ", "A", "a", default_weight=1.8),
    "EH": Vowel("EH", VowelQuality.SHORT_LAX, VowelPosition.FRONT, "ɛ", "EH", "eh", default_weight=2.0),
    "IH": Vowel("IH", VowelQuality.SHORT_LAX, VowelPosition.FRONT, "ɪ", "IH", "ih", default_weight=2.0),
    "AA": Vowel("AA", VowelQuality.SHORT_LAX, VowelPosition.BACK, "ɑ", "AH", "ah", default_weight=2.2),
    "AH": Vowel("AH", VowelQuality.SHORT_LAX, VowelPosition.CENTRAL, "ʌ", "UH", "uh", default_weight=1.2),

    # Long / tense vowels (often in open syllables or name endings)
    "IY": Vowel("IY", VowelQuality.LONG_TENSE, VowelPosition.FRONT, "i", "EE", "ee", default_weight=2.5),
    "EY": Vowel("EY", VowelQuality.LONG_TENSE, VowelPosition.FRONT, "eɪ", "AY", "ay", default_weight=2.5),
    "OW": Vowel("OW", VowelQuality.LONG_TENSE, VowelPosition.BACK, "oʊ", "OH", "oh", default_weight=2.8),
    "UW": Vowel("UW", VowelQuality.LONG_TENSE, VowelPosition.BACK, "u", "OO", "oo", default_weight=2.0),

    # Schwa (unstressed reduced vowel)
    "AX": Vowel("AX", VowelQuality.SCHWA, VowelPosition.CENTRAL, "ə", "UH", "uh", default_weight=1.0),
}


# Common name endings sound patterns (for syllable builder / ending bias)
# e.g., -a, -o, -i, -y, -en, -an, -on, -el, -ar, -is
NAME_ENDINGS = [
    # (vowel_key, optional_coda)
    ("AX", None),   # -a (schwa)
    ("OW", None),   # -o
    ("IY", None),   # -i / -y
    ("EH", "n"),    # -en
    ("AE", "n"),    # -an
    ("AA", "n"),    # -on
    ("EH", "l"),    # -el
    ("AA", "r"),    # -ar
    ("IH", "s"),    # -is
]
