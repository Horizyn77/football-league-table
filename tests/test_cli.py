"""Tests for the command-line interface: success paths and usage/validation errors."""

import io

import pytest

from league.cli import main

HEADER = "date,home_team,away_team,home_goals,away_goals"
SAMPLE = "\n".join(
    [
        HEADER,
        "1974-08-17,Arsenal,Ipswich Town,0,1",
        "1974-08-24,Ipswich Town,Burnley,2,0",
        "",
    ]
)


def run(argv, stdin_text=""):
    stdin = io.StringIO(stdin_text)
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = main(argv, stdin=stdin, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


# --- success paths ---------------------------------------------------------


def test_reads_stdin_writes_stdout() -> None:
    code, out, err = run(["--week", "2"], stdin_text=SAMPLE)
    assert code == 0
    assert err == ""
    lines = out.splitlines()
    assert lines[0] == (
        "position,team,played,won,drawn,lost,goals_for,goals_against,goal_average,points"
    )
    # Ipswich Town: 2 wins, GA 3/0 = inf, 4 points -> top.
    assert lines[1] == "1,Ipswich Town,2,2,0,0,3,0,inf,4"


def test_input_and_output_files(tmp_path) -> None:
    input_file = tmp_path / "results.csv"
    output_file = tmp_path / "table.csv"
    input_file.write_text(SAMPLE, encoding="utf-8")
    code, out, err = run(["--input", str(input_file), "--output", str(output_file), "--week", "2"])
    assert code == 0
    assert out == ""  # went to the file, not stdout
    written = output_file.read_text(encoding="utf-8")
    assert written.startswith("position,team,")
    assert "\r" not in written


def test_points_per_win_is_configurable() -> None:
    code, out, _ = run(["--week", "2", "--points-per-win", "3"], stdin_text=SAMPLE)
    assert code == 0
    # Ipswich two wins -> 6 points under 3-per-win.
    assert out.splitlines()[1].endswith(",6")


def test_tiebreak_choice_accepted() -> None:
    code, _, err = run(["--week", "2", "--tiebreak", "goal-difference"], stdin_text=SAMPLE)
    assert code == 0 and err == ""


# --- usage / validation errors ---------------------------------------------


def test_week_and_until_are_mutually_exclusive() -> None:
    with pytest.raises(SystemExit) as exc:
        run(["--week", "2", "--until", "1974-08-24"], stdin_text=SAMPLE)
    assert exc.value.code == 2


def test_neither_week_nor_until() -> None:
    with pytest.raises(SystemExit) as exc:
        run([], stdin_text=SAMPLE)
    assert exc.value.code == 2


def test_week_less_than_one(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--week", "0"], stdin=io.StringIO(SAMPLE), stdout=io.StringIO())
    assert exc.value.code == 2
    assert "week must be 1 or greater" in capsys.readouterr().err


def test_bad_until_date(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--until", "31-12-1974"], stdin=io.StringIO(SAMPLE), stdout=io.StringIO())
    assert exc.value.code == 2
    assert "not a valid YYYY-MM-DD" in capsys.readouterr().err


def test_bad_season_start_date(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(
            ["--week", "2", "--season-start", "nonsense"],
            stdin=io.StringIO(SAMPLE),
            stdout=io.StringIO(),
        )
    assert exc.value.code == 2
    assert "not a valid YYYY-MM-DD" in capsys.readouterr().err


def test_season_start_later_than_earliest_match() -> None:
    code, out, err = run(["--week", "2", "--season-start", "1974-09-01"], stdin_text=SAMPLE)
    assert code == 1
    assert out == ""
    assert err.startswith("error: ")
    assert "later than the earliest match date" in err


def test_data_error_reports_row_number() -> None:
    bad = "\n".join([HEADER, "1974-08-17,Arsenal,Arsenal,0,1"])
    code, out, err = run(["--week", "1"], stdin_text=bad)
    assert code == 1
    assert err == "error: row 2: Arsenal cannot play itself\n"


def test_missing_input_file_is_reported(tmp_path) -> None:
    missing = tmp_path / "nope.csv"
    code, out, err = run(["--input", str(missing), "--week", "1"])
    assert code == 1
    assert err.startswith("error: cannot read input")
