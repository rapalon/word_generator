"""Euphony scoring model for American English invented words."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from company_name.phonemes import PhoneticClass
from company_name.syllables import Syllable

DATA_DIR = Path(__file__).parent / "data"
BIGRAMS_JSON = DATA_DIR / "bigrams.json"


@dataclass
class ScorerWeights:
    open_syllables: float = 20.0
    sonorants: float = 16.0
    cluster_penalty: float = 8.0
    stress_pattern: float = 14.0
    length_bonus: float = 10.0
    memorability: float = 8.0
    pronounceability: float = 16.0
    radio_test: float = 16.0


@dataclass
class EuphonyScore:
    total: int
    open_syllable_score: float
    sonorant_score: float
    cluster_penalty_score: float
    stress_score: float
    length_score: float
    memorability_score: float
    pronounceability_score: float
    radio_test_score: float


class EuphonyScorer:
    """Calculates a 0-100 euphony score for American English brand and fantasy names."""

    def __init__(self, weights: ScorerWeights | None = None) -> None:
        self.weights = weights if weights is not None else ScorerWeights()
        self._bigram_log_probs: dict[str, float] = {}
        if BIGRAMS_JSON.exists():
            try:
                data = json.loads(BIGRAMS_JSON.read_text(encoding="utf-8"))
                self._bigram_log_probs = data.get("log_probs", {})
            except Exception:
                self._bigram_log_probs = {}

    def score(self, spelling: str, syllables: Sequence[Syllable]) -> EuphonyScore:
        clean = spelling.lower().strip()
        n_syl = len(syllables)

        # 1. Share of open syllables (0.0 to 1.0)
        open_count = sum(1 for s in syllables if s.is_open)
        open_ratio = open_count / max(1, n_syl)
        open_score = open_ratio * self.weights.open_syllables

        # 2. Share of sonorants (l, m, n, r)
        total_consonants = 0
        sonorant_count = 0
        has_plosive = False
        has_sonorant = False
        has_cluster = False

        for s in syllables:
            if s.onset:
                total_consonants += 1
                if s.onset.is_cluster:
                    has_cluster = True
                    if any(c in s.onset.symbol for c in "lmnr"):
                        sonorant_count += 0.8
                    if any(c in s.onset.symbol for c in "kptbdg"):
                        has_plosive = True
                else:
                    if s.onset.phonetic_class == PhoneticClass.SONORANT:
                        sonorant_count += 1
                        has_sonorant = True
                    elif s.onset.phonetic_class == PhoneticClass.PLOSIVE:
                        has_plosive = True
            if s.coda:
                total_consonants += 1
                if s.coda.phonetic_class == PhoneticClass.SONORANT:
                    sonorant_count += 1
                    has_sonorant = True
                elif s.coda.phonetic_class == PhoneticClass.PLOSIVE:
                    has_plosive = True

        sonorant_ratio = sonorant_count / max(1, total_consonants)
        sonorant_score = sonorant_ratio * self.weights.sonorants

        # 3. Cluster penalty
        cluster_penalty = self.weights.cluster_penalty if has_cluster else 0.0

        # 4. Stress pattern bonus
        # Cutler & Carter: American content words favor first-syllable stress
        if n_syl >= 1 and syllables[0].is_stressed:
            stress_score = self.weights.stress_pattern
        elif n_syl == 3 and syllables[1].is_stressed and syllables[1].is_heavy:
            # Penultimate stress on heavy middle syllable is also very natural in English
            stress_score = self.weights.stress_pattern * 0.85
        else:
            stress_score = self.weights.stress_pattern * 0.4

        # 5. Length bonus (2-3 syllables is the sweet spot for brand names)
        if n_syl == 2:
            length_score = self.weights.length_bonus
        elif n_syl == 3:
            length_score = self.weights.length_bonus * 0.95
        elif n_syl == 1:
            length_score = self.weights.length_bonus * 0.50
        else:  # 4 syllables
            length_score = self.weights.length_bonus * 0.40

        # 6. Memorability (both plosive and sonorant present)
        memorability_score = (
            self.weights.memorability if (has_plosive and has_sonorant) else self.weights.memorability * 0.3
        )

        # 7. Pronounceability / Bigram frequency
        bigram_scores: list[float] = []
        for i in range(len(clean) - 1):
            bg = clean[i:i + 2]
            # Standard English log probs range from -1.5 (very common, e.g. 'in', 'er') to -4.5 (rare)
            log_p = self._bigram_log_probs.get(bg, -5.0)
            # Map log_p [-5.0, -1.5] -> [0.0, 1.0]
            norm = max(0.0, min(1.0, (log_p - (-5.0)) / ((-1.5) - (-5.0))))
            bigram_scores.append(norm)

        avg_fluency = sum(bigram_scores) / max(1, len(bigram_scores)) if bigram_scores else 0.5
        pronounceability_score = avg_fluency * self.weights.pronounceability

        # 8. Radio Test (Telephone intelligibility & spelling transparency)
        radio_test_score = self.calculate_radio_test(clean, syllables)

        # Calculate final total
        raw_total = (
            open_score
            + sonorant_score
            - cluster_penalty
            + stress_score
            + length_score
            + memorability_score
            + pronounceability_score
            + radio_test_score
        )
        total_score = max(0, min(100, round(raw_total)))

        return EuphonyScore(
            total=total_score,
            open_syllable_score=round(open_score, 1),
            sonorant_score=round(sonorant_score, 1),
            cluster_penalty_score=round(cluster_penalty, 1),
            stress_score=round(stress_score, 1),
            length_score=round(length_score, 1),
            memorability_score=round(memorability_score, 1),
            pronounceability_score=round(pronounceability_score, 1),
            radio_test_score=round(radio_test_score, 1),
        )

    def calculate_radio_test(self, clean_spelling: str, syllables: Sequence[Syllable]) -> float:
        """Evaluate the 'Radio Test' (telephone/low-bandwidth intelligibility & spelling clarity).

        Factors:
        - Spelling ambiguity: letter 'c' (C vs K confusion), final 'y'/'ee' (Y vs I vs EE), doubled vowels
        - Telephone confusion: 'm' vs 'n' nasal ambiguity, confusable stop pairs (b/v, p/b, t/d)
        - Phonetic transparency: words spelled exactly as they sound with clean open vowels (-a, -o)
        """
        clarity = 1.0

        # --- A. Spelling Ambiguity (Listener asks: "How do you spell that?") ---
        # Letter 'c' for /k/ sound creates instant spelling confusion ("C or K?")
        if "c" in clean_spelling:
            clarity -= 0.20

        # Final 'y' or 'ee' vs 'i' ambiguity ("Is that with a Y or an I or double E?")
        if clean_spelling.endswith("y") or clean_spelling.endswith("ee"):
            clarity -= 0.15
        elif clean_spelling.endswith("i"):
            clarity -= 0.05

        # Doubled vowels ('ee', 'oo') prompt "Is that double E/O?"
        if "ee" in clean_spelling or "oo" in clean_spelling:
            clarity -= 0.10

        # Letter 'x' (ambiguous /z/ vs /ks/)
        if "x" in clean_spelling:
            clarity -= 0.15

        # --- B. Telephone Acoustic Confusion (Bandwidth limit 300-3400Hz) ---
        # Nasal confusion: 'm' and 'n' are the #1 most confusable sounds over telephone lines
        if "m" in clean_spelling and "n" in clean_spelling:
            clarity -= 0.15

        # Voicing confusion pairs in low-bandwidth audio:
        if ("b" in clean_spelling and "v" in clean_spelling) or \
           ("p" in clean_spelling and "b" in clean_spelling) or \
           ("t" in clean_spelling and "d" in clean_spelling):
            clarity -= 0.10

        # Consonant clusters can get clipped or muffled in telephone codecs
        has_cluster = any(s.onset and s.onset.is_cluster for s in syllables)
        if has_cluster:
            clarity -= 0.12

        # --- C. Bonuses for High Acoustic Salience ---
        # Words ending in clear open vowels (-a, -o) have great vowel formant salience
        if clean_spelling.endswith("a") or clean_spelling.endswith("o"):
            clarity += 0.10

        # Clamp between 0.0 and 1.0
        norm_clarity = max(0.0, min(1.0, clarity))
        return norm_clarity * self.weights.radio_test
