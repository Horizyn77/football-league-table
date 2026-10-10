"""Tests for CSV parsing and the validation rules."""

from datetime import date

import pytest

from league.models import Match
from league.parsing import ParseError, parse_matches

HEADER = "date,home_team,away_team,home_goals,away_goals"


def lines(*rows: str) -> list[str]:
    return [HEADER, *rows]


def test_parses_a_valid_match() -> None:
    matches = parse_matches(lines("1974-08-17,Birmingham City,Middlesbrough,0,3"))
    assert matches == [Match(date(1974, 8, 17), "Birmingham City", "Middlesbrough", 0, 3)]


def test_accepts_utf8_bom_on_header() -> None:
    matches = parse_matches(["﻿" + HEADER, "1974-08-17,Arsenal,Ipswich Town,0,1"])
    assert matches[0].home_team == "Arsenal"


def test_accepts_crlf_line_endings() -> None:
    # csv.reader is fed already-split lines; a stray CR must not leak into a field.
    matches = parse_matches([HEADER + "\r\n", "1974-08-17,Arsenal,Ipswich Town,0,1\r\n"])
    assert matches[0].away_goals == 1
    assert matches[0].away_team == "Ipswich Town"


def test_skips_blank_lines() -> None:
    matches = parse_matches([HEADER, "", "1974-08-17,Arsenal,Ipswich Town,0,1", ""])
    assert len(matches) == 1


def test_bad_header_is_rejected() -> None:
    with pytest.raises(ParseError) as exc:
        parse_matches(["home,away,score", "x"])
    assert exc.value.row == 1


def test_wrong_column_count() -> None:
    with pytest.raises(ParseError) as exc:
        parse_matches(lines("1974-08-17,Arsenal,Ipswich Town,0"))
    assert exc.value.row == 2
    assert "columns" in exc.value.reason


def test_empty_team_name() -> None:
    with pytest.raises(ParseError) as exc:
        parse_matches(lines("1974-08-17,,Ipswich Town,0,1"))
    assert "home team is empty" in exc.value.reason


def test_team_playing_itself() -> None:
    with pytest.raises(ParseError) as exc:
        parse_matches(lines("1974-08-17,Arsenal,Arsenal,0,1"))
    assert "cannot play itself" in exc.value.reason


def test_non_integer_score() -> None:
    with pytest.raises(ParseError) as exc:
        parse_matches(lines("1974-08-17,Arsenal,Ipswich Town,x,1"))
    assert "not an integer" in exc.value.reason


def test_float_score_is_not_an_integer() -> None:
    with pytest.raises(ParseError) as exc:
        parse_matches(lines("1974-08-17,Arsenal,Ipswich Town,1.5,1"))
    assert "not an integer" in exc.value.reason


def test_negative_score() -> None:
    with pytest.raises(ParseError) as exc:
        parse_matches(lines("1974-08-17,Arsenal,Ipswich Town,-1,1"))
    assert "negative" in exc.value.reason


def test_unparseable_date() -> None:
    with pytest.raises(ParseError) as exc:
        parse_matches(lines("17-08-1974,Arsenal,Ipswich Town,0,1"))
    assert "valid YYYY-MM-DD" in exc.value.reason


def test_dates_going_backwards() -> None:
    with pytest.raises(ParseError) as exc:
        parse_matches(
            lines(
                "1974-08-20,Arsenal,Ipswich Town,0,1",
                "1974-08-17,Chelsea,Burnley,2,2",
            )
        )
    assert "before the previous" in exc.value.reason


def test_same_date_is_allowed() -> None:
    matches = parse_matches(
        lines(
            "1974-08-17,Arsenal,Ipswich Town,0,1",
            "1974-08-17,Chelsea,Burnley,2,2",
        )
    )
    assert len(matches) == 2


def test_team_plays_twice_on_same_date() -> None:
    with pytest.raises(ParseError) as exc:
        parse_matches(
            lines(
                "1974-08-17,Arsenal,Ipswich Town,0,1",
                "1974-08-17,Arsenal,Chelsea,2,2",
            )
        )
    assert "more than once" in exc.value.reason


def test_same_team_pairing_on_different_dates_is_fine() -> None:
    matches = parse_matches(
        lines(
            "1974-08-17,Arsenal,Ipswich Town,0,1",
            "1974-08-24,Arsenal,Chelsea,2,2",
        )
    )
    assert len(matches) == 2
