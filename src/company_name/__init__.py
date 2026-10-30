"""American English euphony-based invented word generator."""

from __future__ import annotations

from company_name.analyzer import WordAnalyzer, WordDiagnostic, format_diagnostic_report
from company_name.cli import main
from company_name.generator import WordGenerator, WordResult
from company_name.phonemes import Consonant, Vowel, PhoneticClass, VowelQuality
from company_name.presets import GeneratorConfig, get_preset
from company_name.scorer import EuphonyScorer, ScorerWeights, EuphonyScore
from company_name.syllables import Syllable

__version__ = "0.1.0"

__all__ = [
    "WordGenerator",
    "WordResult",
    "WordAnalyzer",
    "WordDiagnostic",
    "format_diagnostic_report",
    "GeneratorConfig",
    "get_preset",
    "Syllable",
    "Consonant",
    "Vowel",
    "PhoneticClass",
    "VowelQuality",
    "EuphonyScorer",
    "ScorerWeights",
    "EuphonyScore",
    "main",
]
