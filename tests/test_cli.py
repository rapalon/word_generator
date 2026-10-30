"""Unit tests for the command-line interface."""

import json
from company_name.cli import main
from company_name.generator import WordResult


def test_cli_table_run(capsys):
    ret = main(["--count", "3", "--preset", "balanced", "--seed", "123"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Spelling" in captured.out
    assert "Respelling" in captured.out
    assert "IPA" in captured.out
    assert "Score" in captured.out


def test_cli_json_run(capsys):
    ret = main(["--count", "2", "--format", "json", "--seed", "123"])
    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 2
    assert "spelling" in data[0]
    assert "respelling" in data[0]
    assert "ipa" in data[0]
    assert "score" in data[0]


def test_cli_csv_run(capsys):
    ret = main(["--count", "2", "--format", "csv", "--seed", "123"])
    assert ret == 0
    captured = capsys.readouterr()
    lines = [line.strip() for line in captured.out.strip().splitlines() if line.strip()]
    assert len(lines) == 3  # header + 2 rows
    assert lines[0] == "Spelling,Respelling,IPA,Syllables,Preset,Score"


def test_cli_words_format_run(capsys):
    ret = main(["--count", "3", "--format", "words", "--seed", "123"])
    assert ret == 0
    captured = capsys.readouterr()
    words = [w.strip() for w in captured.out.strip().split(", ")]
    assert len(words) == 3
    # No headers, no pipes, no brackets
    assert "|" not in captured.out
    assert "{" not in captured.out


def test_cli_words_only_flag_run(capsys):
    ret = main(["--count", "4", "-w", "--seed", "123"])
    assert ret == 0
    captured = capsys.readouterr()
    words = [w.strip() for w in captured.out.strip().split(", ")]
    assert len(words) == 4
    assert "|" not in captured.out


def test_cli_lines_format_run(capsys):
    ret = main(["--count", "3", "--format", "lines", "--seed", "123"])
    assert ret == 0
    captured = capsys.readouterr()
    lines = [line.strip() for line in captured.out.strip().splitlines() if line.strip()]
    assert len(lines) == 3
    assert "|" not in captured.out
    assert "," not in captured.out


def test_cli_lines_flag_run(capsys):
    ret = main(["--count", "5", "-l", "--seed", "123"])
    assert ret == 0
    captured = capsys.readouterr()
    lines = [line.strip() for line in captured.out.strip().splitlines() if line.strip()]
    assert len(lines) == 5
    assert "|" not in captured.out
    assert "," not in captured.out
