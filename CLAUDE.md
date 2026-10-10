# CLAUDE.md

Instructions for AI assistants working in this repository. Read this file fully before doing anything.

## Project

A production-quality command-line application that reads football match results
(CSV) and writes a league standing table (CSV). It is used to produce the
**English First Division table for week 10 of the 1974/75 season**. The tool must
work for any week, not just 10.

- Language: **Python 3.10+**, standard library only at runtime.
- Must run on macOS and Linux with plain `python3` commands (developed on Windows via WSL2).
- Dev dependencies (`pytest`, `ruff`) live in `requirements-dev.txt`. Never commit installed packages.

## Environment and commands

Always use a virtualenv at `.venv`. Never `pip install` globally.

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

python3 -m pytest                      # run all tests
ruff check . && ruff format --check .  # lint and format check
python3 -m league --input data/results.csv --week 10 --season-start 1974-08-17 --output out/week10_table.csv
python3 -m league --until 1974-10-19 --season-start 1974-08-17 < data/results.csv > out/week10_table.csv
```

Use `python3`, not `python`, in every command and doc.

## Domain rules (1974/75 English First Division)

These are NOT the modern rules. Never "correct" them to modern rules.

- **2 points for a win**, 1 for a draw, 0 for a loss. (3 points per win began in 1981.)
- **Ranking:** points, then **goal average** = goals for / goals against (higher is better).
  Goal difference is NOT used. (It replaced goal average in 1976/77.)
- **Goal average edge cases:** goals against 0 and goals for > 0 is infinite (ranks first among
  equals, written as `inf` in output). Both 0 gives 0.0.
- **Final tie-break:** team name, alphabetical (A to Z), so output is deterministic. The real
  site's table orders exact ties this way (e.g. Burnley before Newcastle United at week 10).
- Points per win and the tie-break method are configurable via CLI flags but default to the
  rules above.
- Only First Division league matches. No cup or international games.

### Definition of "week N"

- Week 1 starts on the season start date. `--season-start YYYY-MM-DD` sets it; if omitted it
  defaults to the earliest match date in the input (1974-08-17, a Saturday). The README and the
  committed week-10 command pass `--season-start 1974-08-17` explicitly so results never depend
  on how much of the season the input file contains.
- Week N is the Nth 7-day block from that date: `week = (date - start).days // 7 + 1`.
- `--until YYYY-MM-DD` is a date-based alternative to `--week`: include every match dated on or
  before that date. `--week` and `--until` are mutually exclusive and exactly one is required.
- The table for week N includes **all matches from week 1 through week N inclusive** (`week <= N`).
- Midweek fixtures fall in the week they are played. Teams can have different games played.
- Week 5 = 1974-09-14 (last games). Week 10 = 1974-10-19 (last games). No First Division
  games were played 20-25 Oct.

## Data

| Path | Purpose |
| --- | --- |
| `data/raw/results_raw.txt` | Raw pasted text, one `== YYYY-MM-DD ==` header per block |
| `data/results.csv` | Cleaned input: `date,home_team,away_team,home_goals,away_goals` |
| `out/week10_table.csv` | Program output for week 10 (committed deliverable) |
| `tests/fixtures/week10_expected.csv` | Expected week-10 table |
| `tests/fixtures/week5_expected.csv` | Expected week-5 table |

Raw file format: tab-separated, one match per line: home team, home goals, away goals, away team,
venue, gate, notes. Team names and scores have trailing spaces. Header lines may have leading
spaces or trailing tabs. Scorer lines and lines containing `Lineups` must be skipped. A match
line is one where fields 2 and 3 are integers.

Known facts about the data (already verified against the source's league tables):

- 148 matches, 22 teams, 19 date headers, dates in ascending order.
- Matches per week 1 to 10: 22, 22, 11, 11, 11, 19, 11, 11, 19, 11.
- Sanity checks: after week 10 Liverpool are 13 played, 9-1-3, 21 for, 8 against, 2.625, 19 points;
  Leicester City have 12 played (the fewest). After week 5 Ipswich Town lead with 12 points
  and 3.250 goal average.
- Both expected tables are checked against the source standings for 1974-10-19 and 1974-09-14.

**Never invent, guess or "fix" a match result, team name or date from memory.** If something
looks wrong, flag it and let the human check the source. Never edit `tests/fixtures/*` or
`data/results.csv` to make a failing test pass.

## Output format

CSV with header:
`position,team,played,won,drawn,lost,goals_for,goals_against,goal_average,points`

Rows in rank order. `goal_average` has 3 decimals (`inf` when goals against is 0 and goals for > 0).
Write UTF-8 with `\n` line endings.

## CLI

`python3 -m league [--input FILE] [--output FILE] (--week N | --until YYYY-MM-DD) [--season-start YYYY-MM-DD] [--points-per-win N] [--tiebreak goal-average|goal-difference]`

- Read stdin when `--input` is omitted; write stdout when `--output` is omitted.
- Exit code 0 on success, non-zero on invalid input or usage.
- Print errors to stderr in the form `error: <row/line>: <reason>`. Never dump a stack trace for bad input.

## Architecture

Package lives at repo root (`league/`) so `python3 -m league` and `python3 -m pytest` work from
the repo root with no install step. Keep concerns separate:

- `league/models.py`: dataclasses (`Match`, `TeamRecord`, `Rules`)
- `league/parsing.py`: read and validate CSV rows into `Match` objects
- `league/table.py`: pure standings logic (no I/O)
- `league/output.py`: format and write the table as CSV
- `league/cli.py` and `league/__main__.py`: argument handling only
- `tools/convert_raw.py`: raw text file to `data/results.csv` (reports match counts per date)
- `tests/`: pytest tests and `fixtures/`

## Validation

Fail with a clear error (row number and reason) on: missing or extra columns, empty team names,
non-integer or negative scores, unparseable dates, a team playing itself, a team playing twice
on the same date, dates that go backwards in the input, `--week` less than 1, an unparseable `--season-start` or
`--until`, giving both or neither of `--week` and `--until`, or a `--season-start` later than the
earliest match date in the input (it would produce week 0 or negative weeks).
Accept both LF and CRLF line endings and a UTF-8 BOM.

## Code conventions

- Type hints everywhere. Format with `ruff format`, lint with `ruff check`.
- Small, pure functions, no global state, no clever one-liners. The human must be able to explain every line.
- Use `pathlib` for paths. Never hardcode path separators or absolute paths.
- Standard library only for runtime code (`csv`, `argparse`, `dataclasses`, `datetime`, `sys`).

## Testing

Write tests with, or before, the code they cover. Required cases:

- Points: 2 per win, 1 per draw; configurable points per win.
- Ranking by points, then goal average (and goal difference when configured).
- Tie-breaks: equal points and goal average sorted alphabetically.
- Goal average edge cases: zero goals against, zero both.
- Week cutoff: week-N matches included, week N+1 excluded; first-week and empty-result behaviour.
- `--season-start`: the same file gives the same week-10 table with and without it; a trimmed
  file starting in September only matches when `--season-start 1974-08-17` is passed.
- `--until`: `--until 1974-10-19` equals `--week 10`; `--until 1974-09-14` equals `--week 5`;
  a date mid-week includes only matches on or before that date.
- CLI usage errors: `--week` with `--until`, neither given, bad dates, season start too late.
- Validation errors for each rule above.
- End-to-end: `data/results.csv` produces exactly `tests/fixtures/week10_expected.csv` and
  `week5_expected.csv`; also via stdin/stdout.
- Raw converter: parses messy lines (trailing spaces, scorer lines, header oddities) correctly.

If a test fails, diagnose first and explain the cause before changing anything.

## Working agreements

- For anything bigger than a small change, propose a plan and wait for approval before coding.
- One concern per change, small commits with meaningful messages.
- Explain non-obvious decisions in comments or the README, and list assumptions in the README.
- Ask before adding a dependency, changing a domain rule, or changing the layout above.
- Do not add features beyond this spec (no web UI, no database, no extra output formats).
- Flag mistakes you notice in your own earlier work as soon as you see them.

## Cross-platform (developed on Windows, reviewed on macOS)

- Developer machine is Windows (PowerShell). Run commands locally as
  `.venv\Scripts\python -m pytest` and `.venv\Scripts\python -m league ...`.
  README and CI use the Unix forms (`python3`, `.venv/bin/python`).
  Never put Windows-only commands in the README.
- Text I/O: always `open(path, encoding="utf-8", newline="")` for CSV. Write output with
  `\n` line endings on every OS (`lineterminator="\n"`). Reconfigure stdin/stdout to UTF-8 and
  stdout to `\n`. Never rely on default encodings.
- Python floor is 3.10 (tested in CI). Do not use newer-only features (`tomllib`,
  `datetime.UTC`, `typing.Self`, `except*`). The README says how to get 3.10+ on a Mac,
  because macOS's default `python3` may be older.
- No shell scripts, `.bat`/`.ps1`, `os.system`, or Windows-only modules (`msvcrt`, `winreg`).
  Everything runs as `python3 -m ...`.
- Filenames and imports are case-sensitive: use lowercase snake_case and match case exactly.
  Do not rely on the executable bit.
- Never commit `Thumbs.db`, `desktop.ini` or `.DS_Store`.
- Tests: use `tmp_path`, never hardcoded temp paths. Compare CSV output as text with `\n`
  endings. No assertions on path separators.

## CI (GitHub Actions)

- `.github/workflows/ci.yml` runs on `ubuntu-latest` and `macos-latest` with Python 3.10 and
  3.12: create a venv, install `requirements-dev.txt`, run `python3 -m pytest`, then run the CLI
  for week 10 and `diff` the result against `out/week10_table.csv`.
- CI is the only proof the code works on macOS, since development is on Windows. Keep it green.
  Never weaken, skip or delete tests to make CI pass.
- The README shows the CI status badge and notes that development was on Windows with macOS
  verified by CI.
- Before delivery, clone the repo fresh and run the README steps verbatim.

## Repository hygiene

- `.gitignore` must include `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `out/*.tmp`
  and `docs/problem_statement.pdf`.
- **Never commit or quote `docs/problem_statement.pdf`.** It is confidential. Refer to requirements
  by summary only.
- Do NOT ignore `.claude/` or `ai/`: they are required submission artefacts.
- Do not mention any employer, company or unrelated project in code, docs or commit messages.
- `README.md` (setup, run, assumptions, how data was sourced and verified) and `AI_REFLECTION.md`
  are required. **`AI_REFLECTION.md` is written by the human. Do not generate it.**
- Keep `.gitattributes` with `* text=auto eol=lf` so line endings are consistent.

## Definition of done

Tests pass from a fresh clone using only the README steps; CI is green on Ubuntu and macOS; lint is clean; week-10 output
is committed in `out/`; both fixtures match the source standings; README, CLAUDE.md,
AI_REFLECTION.md, `.claude/` and `ai/` are all present.
