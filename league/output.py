"""Format and write the ranked table as CSV.

Columns: position,team,played,won,drawn,lost,goals_for,goals_against,goal_average,points
Goal average is printed to 3 decimals, or the literal ``inf`` when a team has conceded
no goals but scored at least one. Output always uses ``\\n`` line endings.
"""

from __future__ import annotations

import csv
import io
import math
from collections.abc import Iterable
from typing import TextIO

from league.models import Rules, TeamRecord

HEADER = [
    "position",
    "team",
    "played",
    "won",
    "drawn",
    "lost",
    "goals_for",
    "goals_against",
    "goal_average",
    "points",
]


def format_goal_average(value: float) -> str:
    """Three decimals, or ``inf`` for an infinite goal average."""
    if math.isinf(value):
        return "inf"
    return f"{value:.3f}"


def table_rows(records: Iterable[TeamRecord], rules: Rules) -> list[list[str]]:
    """Build the CSV cells for each ranked record, numbering positions from 1."""
    rows: list[list[str]] = []
    for position, record in enumerate(records, start=1):
        rows.append(
            [
                str(position),
                record.team,
                str(record.played),
                str(record.won),
                str(record.drawn),
                str(record.lost),
                str(record.goals_for),
                str(record.goals_against),
                format_goal_average(record.goal_average()),
                str(record.points(rules)),
            ]
        )
    return rows


def write_table(records: Iterable[TeamRecord], rules: Rules, stream: TextIO) -> None:
    """Write the header and ranked rows to a text stream using ``\\n`` endings."""
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(table_rows(records, rules))


def render_table(records: Iterable[TeamRecord], rules: Rules) -> str:
    """Return the full table as a CSV string (used by tests and callers)."""
    buffer = io.StringIO()
    write_table(records, rules, buffer)
    return buffer.getvalue()
