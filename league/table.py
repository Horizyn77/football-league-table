"""Pure standings logic: no I/O, no CSV, no argument parsing.

Given a list of Match objects and a Rules, this module filters by week or date,
accumulates per-team records, and ranks them by the 1974/75 rules:

    1. points (descending)
    2. the tie-break value (descending) - goal average by default, goal difference if configured
    3. team name (ascending, A-Z) so exact ties are deterministic
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from league.models import TIEBREAK_GOAL_DIFFERENCE, Match, Rules, TeamRecord


def week_of(match_date: date, season_start: date) -> int:
    """Which week a date falls in. Week 1 starts on the season start date."""
    return (match_date - season_start).days // 7 + 1


def earliest_match_date(matches: Iterable[Match]) -> date:
    """The earliest match date; used as the default season start."""
    return min(match.date for match in matches)


def matches_up_to_week(matches: Iterable[Match], week: int, season_start: date) -> list[Match]:
    """Every match in weeks 1..week inclusive."""
    return [m for m in matches if week_of(m.date, season_start) <= week]


def matches_until(matches: Iterable[Match], cutoff: date) -> list[Match]:
    """Every match played on or before the cutoff date."""
    return [m for m in matches if m.date <= cutoff]


def build_records(matches: Iterable[Match]) -> dict[str, TeamRecord]:
    """Accumulate each team's totals from the given matches.

    A team appears in the result only once it has played at least one of these
    matches, so an empty match list yields an empty table.
    """
    records: dict[str, TeamRecord] = {}
    for match in matches:
        home = records.setdefault(match.home_team, TeamRecord(match.home_team))
        away = records.setdefault(match.away_team, TeamRecord(match.away_team))
        home.record_result(match.home_goals, match.away_goals)
        away.record_result(match.away_goals, match.home_goals)
    return records


def rank(records: Iterable[TeamRecord], rules: Rules) -> list[TeamRecord]:
    """Order records into final table positions under the given rules."""
    return sorted(records, key=lambda record: _sort_key(record, rules))


def standings(matches: Iterable[Match], rules: Rules) -> list[TeamRecord]:
    """Full pipeline for an already-filtered set of matches: build then rank."""
    return rank(build_records(matches).values(), rules)


def _sort_key(record: TeamRecord, rules: Rules):
    """Sort key for ascending sort: smaller tuple = higher table position.

    Points and the tie-break are negated so that larger values sort first; the
    team name stays ascending so an exact tie is broken alphabetically.
    """
    if rules.tiebreak == TIEBREAK_GOAL_DIFFERENCE:
        tiebreak_value = record.goal_difference()
    else:
        tiebreak_value = record.goal_average_exact()
    return (-record.points(rules), -tiebreak_value, record.team)
