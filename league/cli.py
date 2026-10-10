"""Command-line interface: argument handling and wiring only.

Usage:
    python3 -m league [--input FILE] [--output FILE] (--week N | --until YYYY-MM-DD)
        [--season-start YYYY-MM-DD] [--points-per-win N]
        [--tiebreak goal-average|goal-difference]

Reads stdin when --input is omitted and writes stdout when --output is omitted.
All failures print `error: <reason>` to stderr and exit non-zero; no stack traces.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import TextIO

from league.models import (
    DEFAULT_POINTS_PER_WIN,
    TIEBREAK_GOAL_AVERAGE,
    TIEBREAKS,
    Match,
    Rules,
)
from league.output import write_table
from league.parsing import ParseError, parse_matches
from league.table import (
    earliest_match_date,
    matches_until,
    matches_up_to_week,
    standings,
)


class UsageError(Exception):
    """A usage problem detected after argument parsing (e.g. season start too late)."""


class _ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that reports errors as `error: <message>` to match the spec."""

    def error(self, message: str) -> None:  # type: ignore[override]
        self.exit(2, f"error: {message}\n")


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the CLI. Returns an exit code; argument errors exit via argparse (code 2)."""
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr

    parser = _build_parser()
    args = parser.parse_args(argv)
    rules = Rules(points_per_win=args.points_per_win, tiebreak=args.tiebreak)

    try:
        matches = _read_matches(args.input, stdin)
        selected = _select_matches(matches, args)
    except (ParseError, UsageError) as exc:
        print(f"error: {exc}", file=stderr)
        return 1
    except OSError as exc:
        print(f"error: cannot read input: {exc.strerror or exc}", file=stderr)
        return 1

    try:
        _write_output(standings(selected, rules), rules, args.output, stdout)
    except OSError as exc:
        print(f"error: cannot write output: {exc.strerror or exc}", file=stderr)
        return 1
    return 0


def _build_parser() -> _ArgumentParser:
    parser = _ArgumentParser(
        prog="python3 -m league",
        description="Compute a football league table from match results.",
    )
    parser.add_argument("--input", type=Path, help="input CSV file (default: stdin)")
    parser.add_argument("--output", type=Path, help="output CSV file (default: stdout)")

    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--week", type=_week_arg, help="include matches up to and including this week"
    )
    selection.add_argument(
        "--until",
        type=_date_arg,
        metavar="YYYY-MM-DD",
        help="include matches on or before this date",
    )

    parser.add_argument(
        "--season-start",
        type=_date_arg,
        metavar="YYYY-MM-DD",
        help="date week 1 starts (default: earliest match date)",
    )
    parser.add_argument(
        "--points-per-win",
        type=int,
        default=DEFAULT_POINTS_PER_WIN,
        metavar="N",
        help=f"points awarded for a win (default: {DEFAULT_POINTS_PER_WIN})",
    )
    parser.add_argument(
        "--tiebreak",
        choices=TIEBREAKS,
        default=TIEBREAK_GOAL_AVERAGE,
        help=f"tie-break after points (default: {TIEBREAK_GOAL_AVERAGE})",
    )
    return parser


def _week_arg(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not an integer") from None
    if value < 1:
        raise argparse.ArgumentTypeError("week must be 1 or greater")
    return value


def _date_arg(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a valid YYYY-MM-DD date") from None


def _read_matches(input_path: Path | None, stdin: TextIO) -> list[Match]:
    if input_path is None:
        return parse_matches(stdin)
    with open(input_path, encoding="utf-8", newline="") as handle:
        return parse_matches(handle)


def _select_matches(matches: list[Match], args: argparse.Namespace) -> list[Match]:
    if args.until is not None:
        return matches_until(matches, args.until)

    # --week path: resolve the season start, defaulting to the earliest match date.
    if not matches:
        return []
    earliest = earliest_match_date(matches)
    season_start = args.season_start if args.season_start is not None else earliest
    if season_start > earliest:
        raise UsageError(
            f"season start {season_start.isoformat()} is later than the earliest "
            f"match date {earliest.isoformat()}"
        )
    return matches_up_to_week(matches, args.week, season_start)


def _write_output(table: list, rules: Rules, output_path: Path | None, stdout: TextIO) -> None:
    if output_path is None:
        write_table(table, rules, stdout)
        return
    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        write_table(table, rules, handle)
