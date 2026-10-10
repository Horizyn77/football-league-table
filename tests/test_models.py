"""Tests for the domain models and the goal-average helper."""

import math
from fractions import Fraction

from league.models import (
    DEFAULT_POINTS_PER_WIN,
    Rules,
    TeamRecord,
    goal_average,
)


def test_goal_average_normal() -> None:
    assert goal_average(21, 8) == 21 / 8


def test_goal_average_zero_against_is_infinite() -> None:
    assert goal_average(3, 0) == math.inf


def test_goal_average_zero_both_is_zero() -> None:
    assert goal_average(0, 0) == 0.0


def test_record_result_counts_win_draw_loss() -> None:
    record = TeamRecord(team="Liverpool")
    record.record_result(2, 1)  # win
    record.record_result(0, 0)  # draw
    record.record_result(1, 3)  # loss
    assert (record.played, record.won, record.drawn, record.lost) == (3, 1, 1, 1)
    assert (record.goals_for, record.goals_against) == (3, 4)


def test_points_default_rules() -> None:
    record = TeamRecord(team="X", won=9, drawn=1, lost=3)
    # 9 wins * 2 + 1 draw * 1 = 19 (Liverpool at week 10)
    assert record.points(Rules()) == 19
    assert DEFAULT_POINTS_PER_WIN == 2


def test_points_configurable_points_per_win() -> None:
    record = TeamRecord(team="X", won=9, drawn=1, lost=3)
    # Modern 3-points-per-win: 9 * 3 + 1 = 28
    assert record.points(Rules(points_per_win=3)) == 28


def test_goal_difference() -> None:
    record = TeamRecord(team="X", goals_for=21, goals_against=8)
    assert record.goal_difference() == 13


def test_goal_average_exact_is_fraction() -> None:
    record = TeamRecord(team="X", goals_for=11, goals_against=10)
    assert record.goal_average_exact() == Fraction(11, 10)


def test_goal_average_exact_infinite() -> None:
    record = TeamRecord(team="X", goals_for=3, goals_against=0)
    assert record.goal_average_exact() == math.inf
