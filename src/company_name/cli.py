"""Command-line interface for the invented word generator."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from typing import Sequence

from company_name.analyzer import WordAnalyzer, format_diagnostic_report
from company_name.generator import WordGenerator, WordResult


def format_table(results: Sequence[WordResult]) -> str:
    """Format results as an aligned terminal table."""
    if not results:
        return "No words generated matching criteria."

    headers = ["Spelling", "Respelling", "IPA", "Syllables", "Preset", "Score"]
    rows: list[list[str]] = []
    for r in results:
        rows.append([
            r.spelling,
            r.respelling,
            r.ipa,
            r.syllable_breakdown,
            r.preset,
            str(r.score),
        ])

    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(cell))

    # Format header
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator_line = "-+-".join("-" * col_widths[i] for i in range(len(headers)))

    formatted_rows = [
        " | ".join(row[i].ljust(col_widths[i]) if i < len(headers) - 1 else row[i].rjust(col_widths[i])
                   for i in range(len(headers)))
        for row in rows
    ]

    return "\n".join([header_line, separator_line] + formatted_rows)


def format_csv(results: Sequence[WordResult]) -> str:
    """Format results as CSV string."""
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Spelling", "Respelling", "IPA", "Syllables", "Preset", "Score"])
    for r in results:
        writer.writerow([r.spelling, r.respelling, r.ipa, r.syllable_breakdown, r.preset, r.score])
    return output.getvalue().strip()


def format_words(results: Sequence[WordResult]) -> str:
    """Format results as just the words separated by a comma and a space."""
    return ", ".join(r.spelling for r in results)


def format_lines(results: Sequence[WordResult]) -> str:
    """Format results as just the words, one per line."""
    return "\n".join(r.spelling for r in results)


def format_json(results: Sequence[WordResult]) -> str:
    """Format results as JSON string."""
    data = [r.to_dict() for r in results]
    return json.dumps(data, indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="company-name",
        description="Generate natural, euphonic invented brand and fantasy names for American English.",
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=20,
        help="Number of words to generate (default: 20)",
    )
    parser.add_argument(
        "--preset", "-p",
        choices=["balanced", "soft", "crisp", "tolkien", "elvish", "custom"],
        default="balanced",
        help="Sound symbolism preset: balanced, soft, crisp, tolkien (default: balanced)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to JSON or TOML config file (used when --preset is custom)",
    )
    parser.add_argument(
        "--syllables", "-s",
        type=str,
        default=None,
        help="Number of syllables (e.g. 2 or range like 2-3)",
    )
    parser.add_argument(
        "--starts-with",
        type=str,
        default=None,
        help="Filter words starting with specific letters/sounds (e.g. 'Lu', 'K')",
    )
    parser.add_argument(
        "--ends-with",
        type=str,
        default=None,
        help="Filter words ending with specific letters/sounds (e.g. 'ra', 'on', 'is')",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic, reproducible generation",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Minimum euphony score threshold (0-100, default: 0)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["table", "json", "csv", "words", "list", "lines", "line", "plain"],
        default="table",
        help="Output format: table, json, csv, words, lines (default: table)",
    )
    parser.add_argument(
        "--words-only", "-w",
        action="store_true",
        default=False,
        help="Output only the words separated by a comma and a space",
    )
    parser.add_argument(
        "--lines", "-l",
        action="store_true",
        default=False,
        help="Output only the words, one per line (just the words, nothing else)",
    )
    parser.add_argument(
        "--test", "-t", "--analyze",
        dest="test_word",
        type=str,
        default=None,
        help="Test and audit a single word through all quality, euphony, and radio tests",
    )
    parser.add_argument(
        "--allow-real-words",
        action="store_true",
        default=False,
        help="Allow existing English dictionary words (default: false)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    # Ensure Windows console handles UTF-8 for IPA symbols (e.g. ˈ, ɹ, ɑ)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        # Single word test / audit mode
        if args.test_word:
            analyzer = WordAnalyzer()
            diagnostic = analyzer.analyze(args.test_word)

            if args.format == "json":
                print(json.dumps(diagnostic.to_dict(), indent=2, ensure_ascii=False))
            else:
                print(format_diagnostic_report(diagnostic))
            return 0

        generator = WordGenerator(
            preset_name=args.preset,
            custom_config_path=args.config,
            allow_real_words=args.allow_real_words,
            seed=args.seed,
        )

        results = generator.generate(
            count=args.count,
            syllables=args.syllables,
            starts_with=args.starts_with,
            ends_with=args.ends_with,
            min_score=args.min_score,
        )

        if args.lines or args.format in {"lines", "line", "plain"}:
            print(format_lines(results))
        elif args.words_only or args.format in {"words", "list"}:
            print(format_words(results))
        elif args.format == "table":
            print(format_table(results))
        elif args.format == "csv":
            print(format_csv(results))
        elif args.format == "json":
            print(format_json(results))

        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
