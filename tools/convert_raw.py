"""Convert the raw pasted results text into the cleaned input CSV.

Raw format: blocks headed ``== YYYY-MM-DD ==`` (possibly with leading spaces or
trailing tabs), then tab-separated match lines:

    home team <TAB> home goals <TAB> away goals <TAB> away team <TAB> venue <TAB> gate <TAB> notes

Scorer lines and lines mentioning ``Lineups`` are interleaved and must be skipped.
A line is treated as a match only when its 2nd and 3rd tab fields are whole numbers.

Output: ``date,home_team,away_team,home_goals,away_goals`` CSV (UTF-8, ``\\n`` endings),
and a per-date match-count report printed to stdout.

Run from the repository root:

    python3 tools/convert_raw.py
    python3 tools/convert_raw.py --input data/raw/results_raw.txt --output data/results.csv
"""

from __future__ import annotations

import argparse
import csv
import re
from collections.abc import Iterable
from pathlib import Path

HEADER = ["date", "home_team", "away_team", "home_goals", "away_goals"]
_HEADER_RE = re.compile(r"^\s*==\s*(\d{4}-\d{2}-\d{2})\s*==")
_INTEGER_RE = re.compile(r"\d+")

RAW_DEFAULT = Path("data/raw/results_raw.txt")
CSV_DEFAULT = Path("data/results.csv")


def convert(lines: Iterable[str]) -> tuple[list[list[str]], dict[str, int]]:
    """Parse raw lines into CSV rows and a per-date match count.

    Counts are keyed by date in first-seen order; a date header with no following
    match lines still appears with a count of zero so gaps are visible.
    """
    rows: list[list[str]] = []
    counts: dict[str, int] = {}
    current_date: str | None = None

    for line in lines:
        header = _HEADER_RE.match(line)
        if header:
            current_date = header.group(1)
            counts.setdefault(current_date, 0)
            continue

        fields = [field.strip() for field in line.split("\t")]
        if not _is_match_line(fields):
            continue
        if current_date is None:
            # A match before any date header: skip rather than guess a date.
            continue

        home_team, home_goals, away_goals, away_team = fields[:4]
        rows.append([current_date, home_team, away_team, home_goals, away_goals])
        counts[current_date] += 1

    return rows, counts


def _is_match_line(fields: list[str]) -> bool:
    return (
        len(fields) >= 4
        and _INTEGER_RE.fullmatch(fields[1]) is not None
        and _INTEGER_RE.fullmatch(fields[2]) is not None
    )


def write_csv(rows: list[list[str]], output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)


def _report(rows: list[list[str]], counts: dict[str, int]) -> str:
    teams = {row[1] for row in rows} | {row[2] for row in rows}
    report_lines = [f"{match_date}: {count}" for match_date, count in counts.items()]
    report_lines.append(f"total matches: {len(rows)}")
    report_lines.append(f"date headers: {len(counts)}")
    report_lines.append(f"teams: {len(teams)}")
    return "\n".join(report_lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path, default=RAW_DEFAULT)
    parser.add_argument("--output", type=Path, default=CSV_DEFAULT)
    args = parser.parse_args(argv)

    with open(args.input, encoding="utf-8") as handle:
        rows, counts = convert(handle)

    write_csv(rows, args.output)
    print(_report(rows, counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
