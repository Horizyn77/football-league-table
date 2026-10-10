"""Domain models for the league table.

Three small dataclasses plus two tiny helpers. Everything here is plain data and
arithmetic; no I/O, no sorting, no CSV. The 1974/75 First Division scoring rules live
here as named constants so they are impossible to miss and easy to explain in review.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from fractions import Fraction

# 1974/75 First Division: a draw is worth 1 point and a loss 0, regardless of how many
# points a win is worth. Only the points-per-win value is configurable (see Rules), so
# these two stay as fixed constants rather than CLI options.
POINTS_PER_DRAW = 1
POINTS_PER_LOSS = 0

DEFAULT_POINTS_PER_WIN = 2

# The two supported tie-break methods. Goal average is the 1974/75 rule; goal difference
# is offered only because the task asks for it to be configurable.
TIEBREAK_GOAL_AVERAGE = "goal-average"
TIEBREAK_GOAL_DIFFERENCE = "goal-difference"
TIEBREAKS = (TIEBREAK_GOAL_AVERAGE, TIEBREAK_GOAL_DIFFERENCE)


@dataclass(frozen=True)
class Match:
    """A single played First Division match. Immutable once parsed."""

    date: date
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int


@dataclass(frozen=True)
class Rules:
    """The configurable parts of the scoring system.

    Defaults are the 1974/75 rules: 2 points per win, ranked by goal average.
    """

    points_per_win: int = DEFAULT_POINTS_PER_WIN
    tiebreak: str = TIEBREAK_GOAL_AVERAGE


@dataclass
class TeamRecord:
    """A team's running totals. Mutated as matches are applied, then ranked."""

    team: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0

    def record_result(self, goals_for: int, goals_against: int) -> None:
        """Apply one result (from this team's point of view) to the totals."""
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against
        if goals_for > goals_against:
            self.won += 1
        elif goals_for == goals_against:
            self.drawn += 1
        else:
            self.lost += 1

    def points(self, rules: Rules) -> int:
        return (
            self.won * rules.points_per_win
            + self.drawn * POINTS_PER_DRAW
            + self.lost * POINTS_PER_LOSS
        )

    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    def goal_average(self) -> float:
        """Goals for divided by goals against, as a float for display.

        Edge cases per the spec: no goals conceded with goals scored is infinite;
        no goals either way is 0.0.
        """
        return goal_average(self.goals_for, self.goals_against)

    def goal_average_exact(self) -> Fraction | float:
        """Goal average as an exact value for ranking.

        Using Fraction avoids any floating-point rounding deciding the order of two
        close-but-unequal ratios; the infinite case is the one genuine float.
        """
        if self.goals_against == 0:
            return math.inf if self.goals_for > 0 else Fraction(0)
        return Fraction(self.goals_for, self.goals_against)


def goal_average(goals_for: int, goals_against: int) -> float:
    """Goal average for display: inf when nothing is conceded but goals are scored."""
    if goals_against == 0:
        return math.inf if goals_for > 0 else 0.0
    return goals_for / goals_against
