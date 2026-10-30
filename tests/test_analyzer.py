"""Unit tests for WordAnalyzer and single word audit mode."""

import json
from company_name.analyzer import WordAnalyzer, parse_spelling_to_syllables
from company_name.cli import main


def test_parse_spelling_to_syllables():
    # 3-syllable open word
    syls = parse_spelling_to_syllables("Lumora")
    assert len(syls) == 3
    assert syls[0].is_open
    assert syls[1].is_open
    assert syls[2].is_open

    # Word with coda (Kalvin)
    syls_kalvin = parse_spelling_to_syllables("Kalvin")
    assert len(syls_kalvin) == 2
    assert not syls_kalvin[0].is_open  # Kal- has 'l' coda
    assert syls_kalvin[1].coda is not None  # -vin has 'n' coda


def test_word_analyzer_novel_word():
    analyzer = WordAnalyzer()
    diag = analyzer.analyze("Lumora")

    assert diag.spelling == "Lumora"
    assert diag.is_fully_valid
    assert diag.score.total >= 80
    assert diag.syllable_count == 3
    assert diag.radio_test_feedback["score"] > 0
    assert diag.sound_symbolism["soft_percentage"] > 50


def test_word_analyzer_keeps_written_syllables():
    analyzer = WordAnalyzer()
    for _ in range(20):  # spelling re-rendering used to be random ('ra.pe.lon')
        diag = analyzer.analyze("Rapalon")
        assert diag.syllable_breakdown == "ra.pa.lon"


def test_word_analyzer_stressed_a_is_not_schwa():
    diag = WordAnalyzer().analyze("Rapalon")
    assert diag.respelling == "RA-puh-lohn"
    assert diag.ipa == "/ˈɹæpəloʊn/"


def test_word_analyzer_written_reduplication_flagged():
    diag = WordAnalyzer().analyze("Lala")
    redup_check = next(f for f in diag.filter_checks if f.name == "Reduplication")
    assert not redup_check.passed


def test_word_analyzer_real_word_flagged():
    analyzer = WordAnalyzer()
    diag = analyzer.analyze("planet")

    assert not diag.is_fully_valid
    real_word_check = next(f for f in diag.filter_checks if f.name == "Real English Word")
    assert not real_word_check.passed
    assert "Found in English dictionary" in real_word_check.details


def test_word_analyzer_length_flagged():
    analyzer = WordAnalyzer()
    diag = analyzer.analyze("Ox")

    assert not diag.is_fully_valid
    len_check = next(f for f in diag.filter_checks if f.name == "Length Limits")
    assert not len_check.passed


def test_cli_test_word_text_output(capsys):
    ret = main(["--test", "Lumora"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "WORD AUDIT REPORT: LUMORA" in captured.out
    assert "PHONOLOGICAL PROFILE:" in captured.out
    assert "EUPHONY SCORE:" in captured.out
    assert "RADIO TEST DIAGNOSTICS" in captured.out


def test_cli_test_word_json_output(capsys):
    ret = main(["--test", "Lumora", "--format", "json"])
    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["spelling"] == "Lumora"
    assert "filter_checks" in data
    assert "score" in data
    assert "radio_test" in data
