"""Core word generation library and orchestration."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Optional, Sequence

from company_name.filters import WordFilter
from company_name.phonemes import CONSONANTS, VOWELS
from company_name.presets import GeneratorConfig, get_preset
from company_name.scorer import EuphonyScorer, ScorerWeights
from company_name.spelling_mapper import (
    render_syllables_to_spelling,
    render_word_ipa,
    render_word_respelling,
)
from company_name.syllable_builder import SyllableBuilder
from company_name.syllables import Syllable


@dataclass
class WordResult:
    spelling: str
    respelling: str
    ipa: str
    syllable_breakdown: str
    preset: str
    score: int
    score_details: Optional[dict[str, float]] = None

    def to_dict(self) -> dict:
        return asdict(self)


class WordGenerator:
    """Generates invented, natural, and pleasant words for American English speakers."""

    def __init__(
        self,
        config: Optional[GeneratorConfig] = None,
        preset_name: str = "balanced",
        custom_config_path: Optional[str] = None,
        scorer_weights: Optional[ScorerWeights] = None,
        allow_real_words: bool = False,
        allow_reduplication: bool = False,
        seed: Optional[int] = None,
    ) -> None:
        if config is not None:
            self.config = config
        else:
            self.config = get_preset(preset_name, custom_config_path)

        self.seed = seed
        self.rng = random.Random(seed)
        self.builder = SyllableBuilder(self.config, rng=self.rng)
        self.filter = WordFilter(
            allow_real_words=allow_real_words,
            allow_reduplication=allow_reduplication or self.config.allow_reduplication,
            min_length=self.config.min_length,
            max_length=self.config.max_length,
        )
        self.scorer = EuphonyScorer(scorer_weights)

    def generate(
        self,
        count: int = 20,
        syllables: Optional[str | int] = None,
        starts_with: Optional[str] = None,
        ends_with: Optional[str] = None,
        min_score: int = 0,
        oversample_factor: int = 4,
    ) -> list[WordResult]:
        """Generate `count` distinct words ranked by euphony score.

        Generates an oversampled candidate pool, applies filters, computes scores,
        and returns the top `count` words above `min_score`.
        """
        target_pool_size = max(count * oversample_factor, 100)
        candidates: dict[str, WordResult] = {}
        max_attempts = target_pool_size * 25
        attempts = 0

        clean_prefix = starts_with.strip().lower() if starts_with else None
        clean_suffix = ends_with.strip().lower() if ends_with else None

        while len(candidates) < target_pool_size and attempts < max_attempts:
            attempts += 1

            syl_count = self.builder.choose_syllable_count(syllables)
            syl_list = self.builder.build_word(syl_count)

            spelling, breakdown = render_syllables_to_spelling(syl_list, rng=self.rng)

            # Check starts_with constraint
            if clean_prefix and not spelling.lower().startswith(clean_prefix):
                continue

            # Check ends_with constraint
            if clean_suffix and not spelling.lower().endswith(clean_suffix):
                continue

            # Apply rejection filters
            is_valid, _ = self.filter.is_valid(spelling, syllables=syl_list)
            if not is_valid:
                continue

            # Compute representations
            respelling = render_word_respelling(syl_list)
            ipa = render_word_ipa(syl_list)
            score_res = self.scorer.score(spelling, syl_list)

            if score_res.total < min_score:
                continue

            # Avoid duplicates
            if spelling not in candidates:
                candidates[spelling] = WordResult(
                    spelling=spelling,
                    respelling=respelling,
                    ipa=ipa,
                    syllable_breakdown=breakdown,
                    preset=self.config.name,
                    score=score_res.total,
                    score_details={
                        "open_syllables": score_res.open_syllable_score,
                        "sonorants": score_res.sonorant_score,
                        "cluster_penalty": score_res.cluster_penalty_score,
                        "stress_pattern": score_res.stress_score,
                        "length_bonus": score_res.length_score,
                        "memorability": score_res.memorability_score,
                        "pronounceability": score_res.pronounceability_score,
                        "radio_test": score_res.radio_test_score,
                    },
                )

        # Sort descending by score
        ranked = sorted(candidates.values(), key=lambda r: r.score, reverse=True)
        return ranked[:count]
