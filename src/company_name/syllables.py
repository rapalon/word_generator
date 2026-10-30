"""Syllable model and phonological representation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from company_name.phonemes import Consonant, Vowel, VowelQuality


@dataclass
class Syllable:
    nucleus: Vowel
    onset: Optional[Consonant] = None
    coda: Optional[Consonant] = None
    is_stressed: bool = False

    @property
    def is_open(self) -> bool:
        """A syllable is open if it has no coda consonant."""
        return self.coda is None

    @property
    def is_heavy(self) -> bool:
        """A syllable is heavy if it has a coda consonant or a tense/long vowel."""
        return self.coda is not None or self.nucleus.quality == VowelQuality.LONG_TENSE

    def to_ipa(self, include_stress_mark: bool = False) -> str:
        """Render the syllable in American English IPA."""
        parts: list[str] = []
        if include_stress_mark and self.is_stressed:
            parts.append("ˈ")
        if self.onset:
            parts.append(self.onset.ipa)
        parts.append(self.nucleus.ipa)
        if self.coda:
            parts.append(self.coda.ipa)
        return "".join(parts)

    def to_respelling(self) -> str:
        """Render the syllable in pronunciation respelling (stressed in caps)."""
        onset_str = self.onset.respelling if self.onset else ""
        coda_str = self.coda.respelling if self.coda else ""

        if self.is_stressed:
            vowel_str = self.nucleus.stressed_respelling
            raw = f"{onset_str}{vowel_str}{coda_str}".upper()
        else:
            vowel_str = self.nucleus.unstressed_respelling
            raw = f"{onset_str}{vowel_str}{coda_str}".lower()
        return raw
