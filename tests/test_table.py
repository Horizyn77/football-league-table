"""Tests for the pure standings logic: weeks, accumulation and ranking."""

from datetime import date

from league.models import Match, Rules
from league.table import (
    build_records,
    earliest_match_date,
    matches_until,
    matches_up_to_week,
    standings,
    week_of,
)

SEASON_START = date(1974, 8, 17)


def m(d: str, home: str, away: str, hg: int, ag: int) -> Match:
    return Match(date.fromisoformat(d), home, away, hg, ag)


# --- week arithmetic -------------------------------------------------------


def test_week_of_first_day_is_week_one() -> None:
    assert week_of(date(1974, 8, 17), SEASON_START) == 1


def test_week_of_seventh_day_is_week_one() -> None:
    assert week_of(date(1974, 8, 23), SEASON_START) == 1


def test_week_of_eighth_day_is_week_two() -> None:
    assert week_of(date(1974, 8, 24), SEASON_START) == 2


def test_week_of_week_ten_last_day() -> None:
    assert week_of(date(1974, 10, 19), SEASON_START) == 10


def test_earliest_match_date() -> None:
    matches = [m("1974-08-24", "A", "B", 1, 0), m("1974-08-17", "C", "D", 0, 0)]
    assert earliest_match_date(matches) == SEASON_START


# --- filtering -------------------------------------------------------------


def test_week_cutoff_includes_week_n_excludes_n_plus_one() -> None:
    matches = [
        m("1974-08-17", "A", "B", 1, 0),  # week 1
        m("1974-08-24", "A", "C", 2, 0),  # week 2
    ]
    kept = matches_up_to_week(matches, 1, SEASON_START)
    assert kept == [matches[0]]


def test_matches_until_is_inclusive() -> None:
    matches = [
        m("1974-08-17", "A", "B", 1, 0),
        m("1974-08-18", "A", "C", 2, 0),
    ]
    kept = matches_until(matches, date(1974, 8, 17))
    assert kept == [matches[0]]


def test_empty_window_gives_empty_table() -> None:
    assert standings([], Rules()) == []


# --- accumulation ----------------------------------------------------------


def test_build_records_counts_both_sides() -> None:
    records = build_records([m("1974-08-17", "A", "B", 3, 1)])
    assert records["A"].won == 1 and records["A"].goals_for == 3
    assert records["B"].lost == 1 and records["B"].goals_against == 3


# --- ranking ---------------------------------------------------------------


def test_points_then_goal_average_ordering() -> None:
    # Both teams win once (2 pts). Higher goal average ranks first.
    matches = [
        m("1974-08-17", "High", "X", 5, 0),  # High: GA 5/0 handled, use conceding below
        m("1974-08-17", "Low", "Y", 2, 1),  # Low: GA 2/1 = 2.0
        m("1974-08-24", "High", "Z", 3, 1),  # High now 8 for, 1 against => 8.0
    ]
    table = standings(matches, Rules())
    names = [r.team for r in table]
    assert names.index("High") < names.index("Low")


def test_exact_tie_breaks_alphabetically() -> None:
    # Burnley and Leicester both: played, equal points, GA 11/10 exactly.
    matches = [
        m("1974-08-17", "Leicester City", "A", 11, 10),
        m("1974-08-17", "Burnley", "B", 11, 10),
    ]
    table = standings(matches, Rules())
    assert [r.team for r in table][:2] == ["Burnley", "Leicester City"]


def test_zero_goals_against_ranks_first() -> None:
    # A win to nil (infinite goal average) outranks an equal-points high-scoring win.
    matches = [
        m("1974-08-17", "ToNil", "X", 1, 0),  # GA inf
        m("1974-08-17", "HighScore", "Y", 9, 1),  # GA 9.0
    ]
    table = standings(matches, Rules())
    assert table[0].team == "ToNil"


def test_goal_difference_tiebreak_when_configured() -> None:
    # Equal points. A: 5-0 (GD +5, GA inf). B: 10-4 (GD +6, GA 2.5).
    # Under goal difference, B (+6) outranks A (+5); under goal average A (inf) wins.
    matches = [
        m("1974-08-17", "A", "X", 5, 0),
        m("1974-08-17", "B", "Y", 10, 4),
    ]
    by_difference = standings(matches, Rules(tiebreak="goal-difference"))
    assert by_difference[0].team == "B"
    by_average = standings(matches, Rules())
    assert by_average[0].team == "A"
