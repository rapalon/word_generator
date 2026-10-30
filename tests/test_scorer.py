"""Unit tests for the euphony scoring algorithm."""

from company_name.phonemes import ALLOWED_ONSET_CLUSTERS, CONSONANTS, VOWELS
from company_name.scorer import EuphonyScorer, ScorerWeights
from company_name.syllables import Syllable


def test_scorer_range_and_breakdown():
    scorer = EuphonyScorer()
    s1 = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["UW"], is_stressed=True)
    s2 = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["OW"], coda=CONSONANTS["r"], is_stressed=False)
    s3 = Syllable(onset=None, nucleus=VOWELS["AX"], is_stressed=False)

    score_res = scorer.score("Lumora", [s1, s2, s3])
    assert 0 <= score_res.total <= 100
    assert score_res.open_syllable_score > 0
    assert score_res.sonorant_score > 0
    assert score_res.memorability_score > 0


def test_stress_bonus():
    scorer = EuphonyScorer()
    # Trochaic stress gets higher stress score than final stress
    s1_troch = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["AA"], coda=CONSONANTS["r"], is_stressed=True)
    s2_troch = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["OW"], is_stressed=False)
    troch_res = scorer.score("Marlo", [s1_troch, s2_troch])

    s1_iamb = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["AA"], coda=CONSONANTS["r"], is_stressed=False)
    s2_iamb = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["OW"], is_stressed=True)
    iamb_res = scorer.score("Marlo", [s1_iamb, s2_iamb])

    assert troch_res.stress_score > iamb_res.stress_score


def test_cluster_penalty():
    scorer = EuphonyScorer()
    # Word without cluster
    s1 = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["OW"], is_stressed=True)
    s2 = Syllable(onset=CONSONANTS["n"], nucleus=VOWELS["AX"], is_stressed=False)
    clean_score = scorer.score("Lona", [s1, s2])

    # Word with cluster
    s1_c = Syllable(onset=ALLOWED_ONSET_CLUSTERS["fl"], nucleus=VOWELS["OW"], is_stressed=True)
    s2_c = Syllable(onset=CONSONANTS["n"], nucleus=VOWELS["AX"], is_stressed=False)
    cluster_score = scorer.score("Flona", [s1_c, s2_c])
    assert cluster_score.cluster_penalty_score > 0
    assert clean_score.cluster_penalty_score == 0.0


def test_radio_test_spelling_transparency():
    scorer = EuphonyScorer()
    # 'Marlo' is spelled exactly as it sounds, clear open -o ending
    s1 = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["AA"], coda=CONSONANTS["r"], is_stressed=True)
    s2 = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["OW"], is_stressed=False)
    clear_res = scorer.score("Marlo", [s1, s2])

    # Word with ambiguous 'c' (C vs K confusion: 'Lico')
    s1_c = Syllable(onset=CONSONANTS["l"], nucleus=VOWELS["IY"], is_stressed=True)
    s2_c = Syllable(onset=CONSONANTS["k"], nucleus=VOWELS["OW"], is_stressed=False)
    c_res = scorer.score("Lico", [s1_c, s2_c])

    # Word with ambiguous final -y (Y vs I vs EE: 'Dimy')
    s1_y = Syllable(onset=CONSONANTS["d"], nucleus=VOWELS["IH"], is_stressed=True)
    s2_y = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["IY"], is_stressed=False)
    y_res = scorer.score("Dimy", [s1_y, s2_y])

    assert clear_res.radio_test_score > c_res.radio_test_score
    assert clear_res.radio_test_score > y_res.radio_test_score


def test_radio_test_telephone_nasal_confusion():
    scorer = EuphonyScorer()
    # Word without m/n nasal confusion
    s1 = Syllable(onset=CONSONANTS["t"], nucleus=VOWELS["OW"], is_stressed=True)
    s2 = Syllable(onset=CONSONANTS["ɹ"] if "ɹ" in CONSONANTS else CONSONANTS["r"], nucleus=VOWELS["AX"], is_stressed=False)
    tora_res = scorer.score("Tora", [s1, s2])

    # Word with both 'm' and 'n' (Mary vs Nancy telephone confusion)
    s1_mn = Syllable(onset=CONSONANTS["m"], nucleus=VOWELS["OW"], is_stressed=True)
    s2_mn = Syllable(onset=CONSONANTS["n"], nucleus=VOWELS["AX"], is_stressed=False)
    mona_res = scorer.score("Mona", [s1_mn, s2_mn])

    assert tora_res.radio_test_score > mona_res.radio_test_score
