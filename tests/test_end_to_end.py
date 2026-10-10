"""End-to-end tests against the real data and the official week 5/10 fixtures.

These prove the whole pipeline (parse -> filter -> rank -> format) reproduces the
standings from englishfootballleaguetables.co.uk exactly, and that --week, --until
and --season-start behave as specified.
"""

import csv
import io
from pathlib import Path

from league.cli import main

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "results.csv"
FIXTURES = ROOT / "tests" / "fixtures"


def run_cli(argv, stdin_text=""):
    stdin = io.StringIO(stdin_text)
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = main(argv, stdin=stdin, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def fixture_text(name: str) -> str:
    # newline="" so the file's own \n endings are preserved for an exact compare.
    with open(FIXTURES / name, encoding="utf-8", newline="") as handle:
        return handle.read()


def parse_table(csv_text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(csv_text)))


# --- exact reproduction of the official tables -----------------------------


def test_week10_matches_official_fixture() -> None:
    code, out, err = run_cli(["--input", str(DATA), "--week", "10", "--season-start", "1974-08-17"])
    assert code == 0 and err == ""
    assert out == fixture_text("week10_expected.csv")


def test_week5_matches_official_fixture() -> None:
    code, out, _ = run_cli(["--input", str(DATA), "--week", "5", "--season-start", "1974-08-17"])
    assert code == 0
    assert out == fixture_text("week5_expected.csv")


def test_week10_via_stdin_stdout() -> None:
    source = DATA.read_text(encoding="utf-8")
    code, out, _ = run_cli(["--week", "10", "--season-start", "1974-08-17"], stdin_text=source)
    assert code == 0
    assert out == fixture_text("week10_expected.csv")


def test_committed_output_file_matches_program(tmp_path) -> None:
    # The committed deliverable out/week10_table.csv must equal a fresh run.
    code, out, _ = run_cli(["--input", str(DATA), "--week", "10", "--season-start", "1974-08-17"])
    assert code == 0
    committed = (ROOT / "out" / "week10_table.csv").read_text(encoding="utf-8")
    assert out == committed


# --- --until is equivalent to --week at the right dates --------------------


def test_until_week10_date_equals_week10() -> None:
    _, by_until, _ = run_cli(["--input", str(DATA), "--until", "1974-10-19"])
    assert by_until == fixture_text("week10_expected.csv")


def test_until_week5_date_equals_week5() -> None:
    _, by_until, _ = run_cli(["--input", str(DATA), "--until", "1974-09-14"])
    assert by_until == fixture_text("week5_expected.csv")


def test_until_midweek_excludes_later_matches() -> None:
    # 1974-10-15 is mid-week-9; the 10-16 and 10-19 fixtures must be excluded.
    _, midweek, _ = run_cli(["--input", str(DATA), "--until", "1974-10-15"])
    _, full_week10, _ = run_cli(["--input", str(DATA), "--until", "1974-10-19"])
    assert midweek != full_week10
    midweek_played = sum(int(r["played"]) for r in parse_table(midweek))
    week10_played = sum(int(r["played"]) for r in parse_table(full_week10))
    assert midweek_played < week10_played


# --- --season-start controls week numbering --------------------------------


def test_season_start_default_equals_explicit() -> None:
    # The earliest match date is 1974-08-17, so the default must equal passing it.
    _, with_flag, _ = run_cli(
        ["--input", str(DATA), "--week", "10", "--season-start", "1974-08-17"]
    )
    _, without_flag, _ = run_cli(["--input", str(DATA), "--week", "10"])
    assert with_flag == without_flag == fixture_text("week10_expected.csv")


def _september_trimmed_csv() -> str:
    """data/results.csv with only matches from 1974-09-07 (week 4) onward."""
    rows = DATA.read_text(encoding="utf-8").splitlines()
    header, data_rows = rows[0], rows[1:]
    kept = [r for r in data_rows if r.split(",")[0] >= "1974-09-07"]
    return "\n".join([header, *kept]) + "\n"


def test_trimmed_file_needs_season_start_for_correct_weeks() -> None:
    trimmed = _september_trimmed_csv()

    # With the real season start, the earliest kept matches are in week 4, so a
    # week-3 cut is empty.
    _, week3_with_start, _ = run_cli(
        ["--week", "3", "--season-start", "1974-08-17"], stdin_text=trimmed
    )
    assert parse_table(week3_with_start) == []

    # Without it, the earliest kept date becomes week 1, so a week-3 cut is not empty.
    _, week3_without_start, _ = run_cli(["--week", "3"], stdin_text=trimmed)
    assert parse_table(week3_without_start) != []


# --- sanity checks from the project brief ----------------------------------


def test_week10_sanity_numbers() -> None:
    _, out, _ = run_cli(["--input", str(DATA), "--week", "10", "--season-start", "1974-08-17"])
    table = {row["team"]: row for row in parse_table(out)}

    liverpool = table["Liverpool"]
    assert liverpool["position"] == "1"
    assert [liverpool[k] for k in ("played", "won", "drawn", "lost")] == ["13", "9", "1", "3"]
    assert [liverpool[k] for k in ("goals_for", "goals_against")] == ["21", "8"]
    assert liverpool["goal_average"] == "2.625"
    assert liverpool["points"] == "19"

    fewest = min(int(row["played"]) for row in table.values())
    assert fewest == 12
    assert table["Leicester City"]["played"] == "12"


def test_week5_sanity_numbers() -> None:
    _, out, _ = run_cli(["--input", str(DATA), "--week", "5", "--season-start", "1974-08-17"])
    table = parse_table(out)
    leader = table[0]
    assert leader["team"] == "Ipswich Town"
    assert leader["points"] == "12"
    assert leader["goal_average"] == "3.250"
