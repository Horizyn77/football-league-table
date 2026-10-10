"""Read and validate CSV rows into Match objects.

Input columns (with header): date,home_team,away_team,home_goals,away_goals

Every rejection raises ParseError carrying the 1-based row number and a plain-English
reason, so the CLI can print `error: row N: <reason>` without a stack trace. A leading
UTF-8 BOM and both LF and CRLF line endings are tolerated.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Iterable
from datetime import date

from league.models import Match

EXPECTED_HEADER = ["date", "home_team", "away_team", "home_goals", "away_goals"]
_BOM = "﻿"


class ParseError(Exception):
    """A single row (or the header) failed validation."""

    def __init__(self, row: int, reason: str) -> None:
        self.row = row
        self.reason = reason
        super().__init__(f"row {row}: {reason}")


def parse_matches(rows: Iterable[str]) -> list[Match]:
    """Parse validated matches from an iterable of CSV text lines.

    The caller owns opening the file or stdin; this function only reads rows.
    """
    reader = csv.reader(rows)
    matches: list[Match] = []

    last_date: date | None = None
    teams_by_date: dict[date, set[str]] = defaultdict(set)

    for row_number, raw_row in enumerate(reader, start=1):
        if row_number == 1:
            _validate_header(raw_row)
            continue

        fields = _strip_fields(raw_row)
        if not fields or all(value == "" for value in fields):
            # Tolerate blank separator lines.
            continue
        if len(fields) != len(EXPECTED_HEADER):
            raise ParseError(
                row_number,
                f"expected {len(EXPECTED_HEADER)} columns, got {len(fields)}",
            )

        match = _build_match(fields, row_number)

        if last_date is not None and match.date < last_date:
            raise ParseError(
                row_number,
                f"date {match.date.isoformat()} is before the previous row's "
                f"date {last_date.isoformat()}",
            )
        last_date = match.date

        for team in (match.home_team, match.away_team):
            if team in teams_by_date[match.date]:
                raise ParseError(
                    row_number,
                    f"{team} plays more than once on {match.date.isoformat()}",
                )
            teams_by_date[match.date].add(team)

        matches.append(match)

    return matches


def _validate_header(raw_row: list[str]) -> None:
    header = _strip_fields(raw_row)
    if header[:1]:
        header[0] = header[0].lstrip(_BOM)
    if header != EXPECTED_HEADER:
        expected = ",".join(EXPECTED_HEADER)
        raise ParseError(1, f"expected header {expected!r}, got {','.join(header)!r}")


def _build_match(fields: list[str], row_number: int) -> Match:
    date_text, home_team, away_team, home_goals_text, away_goals_text = fields

    match_date = _parse_date(date_text, row_number)

    if not home_team:
        raise ParseError(row_number, "home team is empty")
    if not away_team:
        raise ParseError(row_number, "away team is empty")
    if home_team == away_team:
        raise ParseError(row_number, f"{home_team} cannot play itself")

    home_goals = _parse_score(home_goals_text, row_number, "home goals")
    away_goals = _parse_score(away_goals_text, row_number, "away goals")

    return Match(
        date=match_date,
        home_team=home_team,
        away_team=away_team,
        home_goals=home_goals,
        away_goals=away_goals,
    )


def _parse_date(value: str, row_number: int) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ParseError(row_number, f"date {value!r} is not a valid YYYY-MM-DD date") from None


def _parse_score(value: str, row_number: int, label: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise ParseError(row_number, f"{label} {value!r} is not an integer") from None
    if number < 0:
        raise ParseError(row_number, f"{label} {value!r} is negative")
    return number


def _strip_fields(raw_row: list[str]) -> list[str]:
    return [value.strip() for value in raw_row]
