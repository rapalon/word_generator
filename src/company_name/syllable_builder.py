"""Syllable builder generating sequences of phonemes respecting American English phonological rules."""

from __future__ import annotations

import random
from typing import Optional, Sequence

from company_name.phonemes import (
    ALLOWED_CODAS,
    ALLOWED_ONSET_CLUSTERS,
    CONSONANTS,
    NAME_ENDINGS,
    VOWELS,
    Consonant,
    PhoneticClass,
    Vowel,
    VowelQuality,
)
from company_name.presets import GeneratorConfig
from company_name.stress import assign_stress_and_reduction
from company_name.syllables import Syllable


class SyllableBuilder:
    def __init__(self, config: GeneratorConfig, rng: Optional[random.Random] = None) -> None:
        self.config = config
        self.rng = rng if rng is not None else random.Random()

        # Build weighted pools
        self._consonant_pool: list[str] = []
        self._consonant_weights: list[float] = []
        for sym, c in CONSONANTS.items():
            if c.can_onset:
                w = self.config.consonant_weights.get(sym, c.default_weight)
                self._consonant_pool.append(sym)
                self._consonant_weights.append(w)

        self._coda_pool: list[str] = []
        self._coda_weights: list[float] = []
        for sym, c in ALLOWED_CODAS.items():
            w = self.config.consonant_weights.get(sym, c.default_weight)
            # Give higher coda probability to sonorants
            if c.phonetic_class == PhoneticClass.SONORANT:
                w *= 2.0
            self._coda_pool.append(sym)
            self._coda_weights.append(w)

        self._cluster_pool: list[str] = list(ALLOWED_ONSET_CLUSTERS.keys())
        self._cluster_weights: list[float] = [
            self.config.cluster_weights.get(k, 1.0) for k in self._cluster_pool
        ]

        self._vowel_pool: list[str] = []
        self._vowel_weights: list[float] = []
        for sym, v in VOWELS.items():
            w = self.config.vowel_weights.get(sym, v.default_weight)
            self._vowel_pool.append(sym)
            self._vowel_weights.append(w)

    def pick_consonant(self) -> Consonant:
        sym = self.rng.choices(self._consonant_pool, weights=self._consonant_weights, k=1)[0]
        return CONSONANTS[sym]

    def pick_coda(self) -> Consonant:
        sym = self.rng.choices(self._coda_pool, weights=self._coda_weights, k=1)[0]
        return ALLOWED_CODAS[sym]

    def pick_cluster(self) -> Consonant:
        sym = self.rng.choices(self._cluster_pool, weights=self._cluster_weights, k=1)[0]
        return ALLOWED_ONSET_CLUSTERS[sym]

    def pick_vowel(self, prefer_tense: bool = False) -> Vowel:
        weights = list(self._vowel_weights)
        if prefer_tense:
            for i, sym in enumerate(self._vowel_pool):
                v = VOWELS[sym]
                if v.quality == VowelQuality.LONG_TENSE:
                    weights[i] *= 2.0
        sym = self.rng.choices(self._vowel_pool, weights=weights, k=1)[0]
        return VOWELS[sym]

    def choose_syllable_count(self, syllable_spec: Optional[str | int] = None) -> int:
        if syllable_spec is not None:
            if isinstance(syllable_spec, int):
                return syllable_spec
            spec_str = str(syllable_spec).strip()
            if "-" in spec_str:
                parts = [int(p) for p in spec_str.split("-") if p.isdigit()]
                if len(parts) == 2 and parts[0] <= parts[1]:
                    return self.rng.randint(parts[0], parts[1])
            elif spec_str.isdigit():
                return int(spec_str)

        # Sample from distribution
        counts = list(self.config.syllable_distribution.keys())
        weights = list(self.config.syllable_distribution.values())
        return self.rng.choices(counts, weights=weights, k=1)[0]

    def build_word(
        self,
        syllable_count: int,
        starts_with: Optional[str] = None,
        ends_with: Optional[str] = None,
    ) -> list[Syllable]:
        """Build a sequence of syllables adhering to euphony rules."""
        for _ in range(50):  # attempts to satisfy constraints
            syllables = self._generate_candidate_syllables(syllable_count)
            syllables = assign_stress_and_reduction(syllables)

            # Check open syllable ratio
            open_count = sum(1 for s in syllables if s.is_open)
            ratio = open_count / len(syllables)
            # Rule: prefer open syllables, target at least 70% on average (or max 1 closed in 2/3 syls)
            if len(syllables) >= 2 and (len(syllables) - open_count) > 1:
                continue

            # Check memorability (plosive + sonorant)
            if self.config.require_memorability:
                all_consonants: list[Consonant] = []
                for s in syllables:
                    if s.onset:
                        all_consonants.append(s.onset)
                    if s.coda:
                        all_consonants.append(s.coda)

                has_plosive = any(
                    c.phonetic_class == PhoneticClass.PLOSIVE or
                    (c.is_cluster and any(p in c.symbol for p in "kptbdg"))
                    for c in all_consonants
                )
                has_sonorant = any(
                    c.phonetic_class == PhoneticClass.SONORANT or
                    (c.is_cluster and any(s in c.symbol for s in "lmnr"))
                    for c in all_consonants
                )

                if not (has_plosive and has_sonorant):
                    self._inject_memorability(syllables, has_plosive, has_sonorant)

            return syllables

        # Fallback to direct generation
        fallback = self._generate_candidate_syllables(syllable_count)
        if self.config.require_memorability:
            self._inject_memorability(fallback, False, False)
        return assign_stress_and_reduction(fallback)

    def _generate_candidate_syllables(self, count: int) -> list[Syllable]:
        syllables: list[Syllable] = []
        cluster_used = False

        for i in range(count):
            is_first = (i == 0)
            is_last = (i == count - 1)

            # Onset selection
            onset: Optional[Consonant] = None
            can_use_cluster = (
                not cluster_used and
                (i <= 1) and
                (self.rng.random() < self.config.cluster_probability)
            )

            # If previous syllable has a coda, cannot follow with a cluster (rule: never 3 consonants)
            if i > 0 and syllables[i - 1].coda is not None:
                can_use_cluster = False

            if can_use_cluster:
                onset = self.pick_cluster()
                cluster_used = True
            else:
                # First syllable can occasionally be vowel-initial (10%), later syllables almost always CV
                if is_first and self.rng.random() < 0.10:
                    onset = None
                else:
                    onset = self.pick_consonant()

            # Nucleus selection
            if is_last and self.rng.random() < 0.65:
                # Favor classic name endings (-a, -o, -i, -en, -an, -on, -el, -ar, -is)
                ending_vowel_key, ending_coda_sym = self.rng.choice(NAME_ENDINGS)
                nucleus = VOWELS[ending_vowel_key]
                coda = CONSONANTS[ending_coda_sym] if ending_coda_sym else None
                syllables.append(Syllable(onset=onset, nucleus=nucleus, coda=coda))
                continue

            # Standard vowel selection
            prefer_tense = (count <= 3 and i == 0) or is_last
            nucleus = self.pick_vowel(prefer_tense=prefer_tense)

            # Coda selection
            coda: Optional[Consonant] = None
            # Only allow coda if open syllable target allows it
            # Syllable is closed (CVC) mostly in final position or clean medial boundary
            if is_last:
                if self.rng.random() < 0.25:  # 75% open final
                    coda = self.pick_coda()
            else:
                # Medial coda allowed rarely (15%), must be a sonorant for clean boundary (e.g. Kal-vin, Mar-lo)
                if self.rng.random() < 0.15:
                    sonorants = [c for c in ALLOWED_CODAS.values() if c.phonetic_class == PhoneticClass.SONORANT]
                    coda = self.rng.choice(sonorants)

            syllables.append(Syllable(onset=onset, nucleus=nucleus, coda=coda))

        return syllables

    def _inject_memorability(
        self,
        syllables: list[Syllable],
        has_plosive: bool,
        has_sonorant: bool,
    ) -> None:
        """Inject missing plosive or sonorant into suitable distinct syllables."""
        plosives = [c for c in CONSONANTS.values() if c.phonetic_class == PhoneticClass.PLOSIVE and c.can_onset]
        sonorants = [c for c in CONSONANTS.values() if c.phonetic_class == PhoneticClass.SONORANT and c.can_onset]

        if not has_plosive and not has_sonorant and len(syllables) >= 2:
            syllables[0].onset = self.rng.choice(plosives)
            syllables[1].onset = self.rng.choice(sonorants)
            return

        if not has_plosive and plosives:
            # Place plosive on a syllable whose onset is not a sonorant
            target_indices = [
                i for i, s in enumerate(syllables)
                if not s.onset or s.onset.phonetic_class != PhoneticClass.SONORANT
            ]
            idx = self.rng.choice(target_indices) if target_indices else 0
            syllables[idx].onset = self.rng.choice(plosives)

        if not has_sonorant and sonorants:
            # Place sonorant on a syllable whose onset is not a plosive
            target_indices = [
                i for i, s in enumerate(syllables)
                if not s.onset or s.onset.phonetic_class != PhoneticClass.PLOSIVE
            ]
            idx = self.rng.choice(target_indices) if target_indices else (1 if len(syllables) > 1 else 0)
            syllables[idx].onset = self.rng.choice(sonorants)
