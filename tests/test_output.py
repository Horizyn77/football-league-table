"""Tests for CSV formatting of the table."""

import math

from league.models import Rules, TeamRecord
from league.output import format_goal_average, render_table


def test_format_goal_average_three_decimals() -> None:
    assert format_goal_average(21 / 8) == "2.625"
    assert format_goal_average(19 / 15) == "1.267"
    assert format_goal_average(1.0) == "1.000"


def test_format_goal_average_infinite() -> None:
    assert format_goal_average(math.inf) == "inf"


def test_format_goal_average_zero() -> None:
    assert format_goal_average(0.0) == "0.000"


def test_render_table_header_and_row() -> None:
    record = TeamRecord(
        team="Liverpool", played=13, won=9, drawn=1, lost=3, goals_for=21, goals_against=8
    )
    text = render_table([record], Rules())
    assert text == (
        "position,team,played,won,drawn,lost,goals_for,goals_against,goal_average,points\n"
        "1,Liverpool,13,9,1,3,21,8,2.625,19\n"
    )


def test_render_empty_table_is_header_only() -> None:
    assert render_table([], Rules()) == (
        "position,team,played,won,drawn,lost,goals_for,goals_against,goal_average,points\n"
    )


def test_render_uses_lf_line_endings_only() -> None:
    record = TeamRecord(team="X", played=1, won=1, goals_for=1, goals_against=0)
    text = render_table([record], Rules())
    assert "\r" not in text
    # Infinite goal average serialises literally.
    assert ",inf," in text
