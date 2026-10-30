"""Diagnostic analyzer and comprehensive word testing engine."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Sequence

from company_name.filters import WordFilter, contains_profanity_or_slur, has_awkward_letter_sequences, load_english_wordlist
from company_name.phonemes import (
    ALLOWED_CODAS,
    ALLOWED_ONSET_CLUSTERS,
    CONSONANTS,
    VOWELS,
    Consonant,
    PhoneticClass,
    Vowel,
    VowelQuality,
)
from company_name.scorer import EuphonyScore, EuphonyScorer, ScorerWeights
from company_name.spelling_mapper import (
    render_word_ipa,
    render_word_respelling,
)
from company_name.stress import assign_stress_and_reduction
from company_name.syllables import Syllable


# Vowel patterns for syllabification
VOWEL_DIGRAPHS = ["ee", "oo", "ay", "ai", "oa", "ea", "ou", "ie", "au", "oi", "oy"]
VOWEL_SINGLE_CHARS = "aeiouy"


def split_spelling(word: str) -> list[dict[str, str]]:
    """Split a word into onset/nucleus/coda letter groups using

    the English Maximal Onset Principle. A word without vowels yields a single
    slice with an empty nucleus.
    """
    clean = word.lower().strip()
    if not clean:
        return []

    # 1. Identify vowel nuclei spans
    # Find all vowel nuclei (digraphs or single vowel characters)
    i = 0
    nuclei_spans: list[tuple[int, int, str]] = []
    while i < len(clean):
        # Check two-letter vowel digraphs
        matched_digraph = False
        if i + 1 < len(clean):
            pair = clean[i:i + 2]
            if pair in VOWEL_DIGRAPHS:
                nuclei_spans.append((i, i + 2, pair))
                i += 2
                matched_digraph = True
        if not matched_digraph:
            if clean[i] in VOWEL_SINGLE_CHARS:
                nuclei_spans.append((i, i + 1, clean[i]))
            i += 1

    if not nuclei_spans:
        return [{"onset": clean, "nucleus": "", "coda": ""}]

    # 2. Syllabification with Maximal Onset Principle
    syllable_slices: list[dict[str, str]] = []
    num_nuclei = len(nuclei_spans)

    for idx, (v_start, v_end, v_text) in enumerate(nuclei_spans):
        # Initial onset (before first vowel)
        if idx == 0:
            onset_str = clean[:v_start]
        else:
            prev_end = nuclei_spans[idx - 1][1]
            intervocalic = clean[prev_end:v_start]

            if not intervocalic:
                onset_str = ""
            elif len(intervocalic) == 1:
                # Single consonant goes to onset (Maximal Onset)
                onset_str = intervocalic
            else:
                # Multiple consonants: check if last 2 form an allowed onset cluster
                if len(intervocalic) >= 2 and intervocalic[-2:] in ALLOWED_ONSET_CLUSTERS:
                    coda_str = intervocalic[:-2]
                    onset_str = intervocalic[-2:]
                else:
                    # Otherwise, last 1 consonant is onset, rest are coda of previous syllable
                    coda_str = intervocalic[:-1]
                    onset_str = intervocalic[-1:]

                # Attach coda to previous syllable slice
                if syllable_slices and coda_str:
                    syllable_slices[-1]["coda"] = coda_str

        # Final coda (after last vowel)
        coda_str = ""
        if idx == num_nuclei - 1:
            coda_str = clean[v_end:]

        syllable_slices.append({
            "onset": onset_str,
            "nucleus": v_text,
            "coda": coda_str,
        })

    return syllable_slices


def parse_spelling_to_syllables(word: str) -> list[Syllable]:
    """Parse an arbitrary English or invented word into Syllable objects using

    the English Maximal Onset Principle.
    """
    clean = word.lower().strip()
    syllable_slices = split_spelling(clean)
    if not syllable_slices:
        return []

    # If no vowels detected, treat whole word as single syllable with schwa
    if not syllable_slices[0]["nucleus"]:
        c = CONSONANTS.get(clean, Consonant(clean, PhoneticClass.PLOSIVE, clean, clean))
        return [Syllable(onset=c, nucleus=VOWELS["AX"])]

    # 3. Map parsed slices to Syllable phoneme models
    result_syllables: list[Syllable] = []
    for s_dict in syllable_slices:
        onset_str = s_dict["onset"]
        v_str = s_dict["nucleus"]
        coda_str = s_dict["coda"]

        # Map onset
        onset_obj: Consonant | None = None
        if onset_str:
            if onset_str in ALLOWED_ONSET_CLUSTERS:
                onset_obj = ALLOWED_ONSET_CLUSTERS[onset_str]
            elif onset_str in CONSONANTS:
                onset_obj = CONSONANTS[onset_str]
            else:
                onset_obj = Consonant(onset_str, PhoneticClass.PLOSIVE, onset_str, onset_str)

        # Map vowel
        vowel_obj = VOWELS["AX"]
        if v_str in {"ee", "i", "y"}:
            vowel_obj = VOWELS["IY"]
        elif v_str in {"oo", "u"}:
            vowel_obj = VOWELS["UW"]
        elif v_str in {"ay", "ai"}:
            vowel_obj = VOWELS["EY"]
        elif v_str in {"oa", "o"}:
            vowel_obj = VOWELS["OW"]
        elif v_str == "e":
            vowel_obj = VOWELS["EH"]
        elif v_str == "a":
            # /æ/; stress assignment reduces it to schwa when unstressed and open
            vowel_obj = VOWELS["AE"]
        elif v_str in VOWELS:
            vowel_obj = VOWELS[v_str]

        # Map coda
        coda_obj: Consonant | None = None
        if coda_str:
            if coda_str in ALLOWED_CODAS:
                coda_obj = ALLOWED_CODAS[coda_str]
            elif coda_str in CONSONANTS:
                coda_obj = CONSONANTS[coda_str]
            else:
                coda_obj = Consonant(coda_str, PhoneticClass.SONORANT, coda_str, coda_str)

        result_syllables.append(Syllable(onset=onset_obj, nucleus=vowel_obj, coda=coda_obj))

    # Apply stress and vowel reduction rules
    assign_stress_and_reduction(result_syllables)
    return result_syllables


@dataclass
class FilterCheckResult:
    name: str
    passed: bool
    details: str


@dataclass
class WordDiagnostic:
    spelling: str
    syllables: list[Syllable]
    syllable_count: int
    syllable_breakdown: str
    respelling: str
    ipa: str
    stress_description: str
    is_fully_valid: bool
    filter_checks: list[FilterCheckResult]
    score: EuphonyScore
    sound_symbolism: dict[str, Any]
    radio_test_feedback: dict[str, Any]
    verdict: str
    rating_label: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "spelling": self.spelling,
            "syllables": self.syllable_breakdown,
            "syllable_count": self.syllable_count,
            "respelling": self.respelling,
            "ipa": self.ipa,
            "stress_pattern": self.stress_description,
            "is_valid": self.is_fully_valid,
            "filter_checks": [asdict(f) for f in self.filter_checks],
            "score": asdict(self.score),
            "sound_symbolism": self.sound_symbolism,
            "radio_test": self.radio_test_feedback,
            "rating_label": self.rating_label,
            "verdict": self.verdict,
        }


class WordAnalyzer:
    """Performs deep diagnostic testing on an arbitrary invented or brand word."""

    def __init__(self, scorer_weights: ScorerWeights | None = None) -> None:
        self.scorer = EuphonyScorer(scorer_weights)
        self.english_words = load_english_wordlist()

    def analyze(self, word: str) -> WordDiagnostic:
        clean = word.strip()
        lowered = clean.lower()

        # 1. Parse syllables & phonetic representation
        syllables = parse_spelling_to_syllables(clean)
        n_syl = len(syllables)

        # Split the word as written; re-rendering phonemes could change its letters
        breakdown = ".".join(
            s["onset"] + s["nucleus"] + s["coda"] for s in split_spelling(clean)
        )
        respelling = render_word_respelling(syllables)
        ipa = render_word_ipa(syllables)

        # 2. Stress description
        stressed_idx = next((i for i, s in enumerate(syllables) if s.is_stressed), 0)
        if n_syl == 1:
            stress_desc = "Single syllable (inherently stressed)"
        elif n_syl == 2:
            stress_desc = "Trochaic (1st syllable stressed - ideal for English brand names)" if stressed_idx == 0 else "Iambic (2nd syllable stressed)"
        elif n_syl == 3:
            if stressed_idx == 0:
                stress_desc = "Antepenultimate (1st syllable stressed - natural English cadence)"
            elif stressed_idx == 1:
                stress_desc = "Penultimate (2nd syllable stressed - Latin stress rule on heavy syllable)"
            else:
                stress_desc = "Ultimate (final syllable stressed)"
        else:
            stress_desc = f"Syllable {stressed_idx + 1} primary stress"

        # 3. Filter checks
        filters: list[FilterCheckResult] = []

        # Check A: English Dictionary Word
        is_real = lowered in self.english_words
        filters.append(FilterCheckResult(
            name="Real English Word",
            passed=not is_real,
            details=f"Found in English dictionary: '{lowered}'" if is_real else "Novel invented word (not in English dictionary)",
        ))

        # Check B: Profanity & Slurs
        is_profane = contains_profanity_or_slur(lowered)
        filters.append(FilterCheckResult(
            name="Profanity & Slurs",
            passed=not is_profane,
            details="Contains offensive or sensitive substring" if is_profane else "Clean (no offensive terms or leetspeak variants)",
        ))

        # Check C: Awkward Letter Sequences
        has_awkward = has_awkward_letter_sequences(clean, syllables=syllables, allow_reduplication=False)
        filters.append(FilterCheckResult(
            name="Letter Sequences",
            passed=not has_awkward,
            details="Contains awkward doubling, 3 consonants in a row, or ambiguous letters" if has_awkward else "Fluid, standard American English orthography",
        ))

        # Check D: Immediate Reduplication
        is_redup = False
        if n_syl >= 2:
            rendered_syls = [s.to_respelling().lower() for s in syllables]
            written_syls = breakdown.split(".")
            is_redup = any(
                rendered_syls[i] == rendered_syls[i + 1] or written_syls[i] == written_syls[i + 1]
                for i in range(len(rendered_syls) - 1)
            )
        filters.append(FilterCheckResult(
            name="Reduplication",
            passed=not is_redup,
            details="Contains repetitive syllable stutter (e.g. 'mimi', 'koko')" if is_redup else "No repetitive syllable stuttering",
        ))

        # Check E: Length Limits (4-9 letters)
        in_length = (4 <= len(clean) <= 9)
        filters.append(FilterCheckResult(
            name="Length Limits",
            passed=in_length,
            details=f"{len(clean)} letters (recommended sweet spot: 4–9 letters)",
        ))

        is_fully_valid = all(f.passed for f in filters)

        # 4. Euphony Score
        score = self.scorer.score(clean, syllables)

        # 5. Radio Test Diagnostics
        radio_feedback = self._evaluate_radio_diagnostics(clean, syllables, score.radio_test_score)

        # 6. Sound Symbolism Profile
        symbolism = self._evaluate_sound_symbolism(clean, syllables)

        # 7. Rating Label & Verdict
        if not is_fully_valid:
            rating_label = "REJECTED (Filter Triggered)"
            verdict = "Does not pass quality filters. Review the flagged issues below."
        elif score.total >= 88:
            rating_label = "EXCELLENT (A+)"
            verdict = "Superb brand fluency: highly melodic, easily memorized, and passes the radio test with flying colors."
        elif score.total >= 80:
            rating_label = "VERY GOOD (A)"
            verdict = "Strong, natural-sounding name with good phonetic balance and high pronounceability."
        elif score.total >= 70:
            rating_label = "GOOD (B)"
            verdict = "Plausible name, though minor phonotactic or acoustic adjustments could enhance fluency."
        else:
            rating_label = "FAIR / WEAK (C)"
            verdict = "Noticeable friction in spelling, syllable weight, or acoustic clarity."

        return WordDiagnostic(
            spelling=clean.capitalize(),
            syllables=syllables,
            syllable_count=n_syl,
            syllable_breakdown=breakdown,
            respelling=respelling,
            ipa=ipa,
            stress_description=stress_desc,
            is_fully_valid=is_fully_valid,
            filter_checks=filters,
            score=score,
            sound_symbolism=symbolism,
            radio_test_feedback=radio_feedback,
            verdict=verdict,
            rating_label=rating_label,
        )

    def _evaluate_radio_diagnostics(self, clean: str, syllables: Sequence[Syllable], score_val: float) -> dict[str, Any]:
        lowered = clean.lower()
        strengths: list[str] = []
        ambiguities: list[str] = []

        # C vs K
        if "c" in lowered:
            ambiguities.append("Letter 'C' introduces C vs K spelling ambiguity (listener may ask: 'With a C or a K?')")
        else:
            strengths.append("Unambiguous plosives ('K', 'T', 'P', 'D', 'B') with no C/K confusion")

        # Endings
        if lowered.endswith(("y", "ee")):
            ambiguities.append("Final '-y' / '-ee' may prompt: 'Is that with an I, Y, or double E?'")
        elif lowered.endswith(("a", "o")):
            strengths.append(f"Clear resonant open vowel ending '-{lowered[-1]}' (crisp over telephone audio)")

        # Nasal m/n
        if "m" in lowered and "n" in lowered:
            ambiguities.append("Contains both 'M' and 'N', risking telephone nasal confusion ('M as in Mary, or N as in Nancy?')")
        else:
            strengths.append("No 'M' vs 'N' nasal confusion over low-bandwidth audio")

        # Doubled vowels
        if "ee" in lowered or "oo" in lowered:
            ambiguities.append("Doubled vowels ('ee'/'oo') require verbal clarification ('Is that double E/O?')")

        verdict_str = "Clear & transparent: high likelihood of immediate, accurate transcription" if score_val >= 14.0 else (
            "Moderate clarity: minor spelling or acoustic confirmation may be requested" if score_val >= 10.0 else
            "Low clarity: high chance of mishearing or requiring spelling letter-by-letter"
        )

        return {
            "score": score_val,
            "max_score": self.scorer.weights.radio_test,
            "strengths": strengths,
            "ambiguities": ambiguities,
            "verdict": verdict_str,
        }

    def _evaluate_sound_symbolism(self, clean: str, syllables: Sequence[Syllable]) -> dict[str, Any]:
        lowered = clean.lower()
        soft_chars = sum(1 for c in lowered if c in "mlnbuow")
        crisp_chars = sum(1 for c in lowered if c in "ktpszie")
        total = max(1, soft_chars + crisp_chars)

        soft_pct = round((soft_chars / total) * 100)
        crisp_pct = 100 - soft_pct

        if soft_pct >= 65:
            profile = "Soft & Smooth (Warm, friendly, human, organic, gentle)"
        elif crisp_pct >= 65:
            profile = "Crisp & Light (Fast, precise, tech-oriented, modern)"
        else:
            profile = "Balanced (Versatile, balanced authority and approachability)"

        return {
            "soft_percentage": soft_pct,
            "crisp_percentage": crisp_pct,
            "profile": profile,
        }


def format_diagnostic_report(diag: WordDiagnostic) -> str:
    """Format the comprehensive diagnostic audit report for terminal output."""
    bar_width = 30
    filled = round((diag.score.total / 100.0) * bar_width)
    bar_str = "█" * filled + "░" * (bar_width - filled)

    lines: list[str] = [
        "=" * 68,
        f"          WORD AUDIT REPORT: {diag.spelling.upper()}",
        "=" * 68,
        "",
        "PHONOLOGICAL PROFILE:",
        f"  • Spelling:          {diag.spelling}",
        f"  • Syllable Split:    {diag.syllable_breakdown} ({diag.syllable_count} syllables)",
        f"  • Respelling:        {diag.respelling}",
        f"  • IPA Transcription: {diag.ipa}",
        f"  • Stress Pattern:    {diag.stress_description}",
        "",
        f"QUALITY & SAFETY FILTERS: [{'PASSED' if diag.is_fully_valid else 'FLAGGED'}]",
    ]

    for f in diag.filter_checks:
        symbol = "[✓]" if f.passed else "[✗]"
        lines.append(f"  {symbol} {f.name:<20} {f.details}")

    lines.extend([
        "",
        f"EUPHONY SCORE: {diag.score.total} / 100  [{diag.rating_label}]",
        f"  [{bar_str}]  {diag.score.total}%",
        f"  • Open Syllables:       {diag.score.open_syllable_score:>4.1f} / 20.0",
        f"  • Sonorant Density:     {diag.score.sonorant_score:>4.1f} / 16.0",
        f"  • Cluster Penalty:      {diag.score.cluster_penalty_score:>4.1f} / -8.0",
        f"  • Stress Rhythm:        {diag.score.stress_score:>4.1f} / 14.0",
        f"  • Length Bonus:         {diag.score.length_score:>4.1f} / 10.0",
        f"  • Memorability:         {diag.score.memorability_score:>4.1f} /  8.0",
        f"  • Bigram Fluency:       {diag.score.pronounceability_score:>4.1f} / 16.0",
        f"  • Radio Test:           {diag.score.radio_test_score:>4.1f} / 16.0",
        "",
        "RADIO TEST DIAGNOSTICS (Telephone Intelligibility & Spelling Clarity):",
        f"  • Radio Score:          {diag.radio_test_feedback['score']} / {diag.radio_test_feedback['max_score']}",
        f"  • Verdict:              {diag.radio_test_feedback['verdict']}",
    ])

    if diag.radio_test_feedback["strengths"]:
        lines.append("  • Strengths:")
        for s in diag.radio_test_feedback["strengths"]:
            lines.append(f"      + {s}")

    if diag.radio_test_feedback["ambiguities"]:
        lines.append("  • Potential Confusions:")
        for a in diag.radio_test_feedback["ambiguities"]:
            lines.append(f"      ! {a}")

    soft_pct = diag.sound_symbolism["soft_percentage"]
    crisp_pct = diag.sound_symbolism["crisp_percentage"]
    lines.extend([
        "",
        "BRAND FEEL & SOUND SYMBOLISM:",
        f"  • Profile:              {diag.sound_symbolism['profile']}",
        f"  • Balance:              {soft_pct}% Soft / {crisp_pct}% Crisp",
        "",
        "OVERALL VERDICT:",
        f"  {diag.verdict}",
        "=" * 68,
    ])

    return "\n".join(lines)
