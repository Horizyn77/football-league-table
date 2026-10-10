"""Tests for the raw-text to CSV converter, including the messy-line cases."""

from tools.convert_raw import convert, write_csv

MESSY = [
    "  == 1974-08-17 ==\t",  # header with leading spaces and a trailing tab
    "",
    "Birmingham City \t0\t3 \tMiddlesbrough\tSt Andrew's\t32,105\t",  # trailing spaces
    "\tLineups \tHickton, Foggon 2 \t \t \t ",  # scorer/lineups line -> skip
    "Manchester City \t4\t0 \tWest Ham United\tMaine Road\t30,240\t",
    "Marsh 2, Doyle, Tueart \tLineups \t\t \t \t ",  # scorer line with numbers -> skip
    " == 1974-08-19 ==",
    "West Ham United \t2\t0 \tLuton Town\tUpton Park\t23,182\t",
    "Bonds, Lampard \tLineups \t",  # scorer line -> skip
]


def test_converts_match_lines_only() -> None:
    rows, counts = convert(MESSY)
    assert rows == [
        ["1974-08-17", "Birmingham City", "Middlesbrough", "0", "3"],
        ["1974-08-17", "Manchester City", "West Ham United", "4", "0"],
        ["1974-08-19", "West Ham United", "Luton Town", "2", "0"],
    ]


def test_counts_per_date_including_empty_header() -> None:
    lines = ["== 1974-08-17 ==", "A \t1\t0 \tB\tV\t1\t", "== 1974-08-18 =="]
    _, counts = convert(lines)
    assert counts == {"1974-08-17": 1, "1974-08-18": 0}


def test_trailing_spaces_are_stripped_from_names_and_scores() -> None:
    rows, _ = convert(["== 1974-08-17 ==", "Everton \t0\t0 \tDerby County\tGoodison\t1\t"])
    assert rows == [["1974-08-17", "Everton", "Derby County", "0", "0"]]


def test_match_before_any_header_is_skipped() -> None:
    rows, counts = convert(["Everton \t0\t0 \tDerby County\tV\t1\t"])
    assert rows == []
    assert counts == {}


def test_write_csv_uses_lf_and_header(tmp_path) -> None:
    out = tmp_path / "results.csv"
    write_csv([["1974-08-17", "A", "B", "1", "0"]], out)
    text = out.read_text(encoding="utf-8")
    assert text == "date,home_team,away_team,home_goals,away_goals\n1974-08-17,A,B,1,0\n"
    assert "\r" not in text
