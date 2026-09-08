from dataclasses import dataclass
from .actions import Action, ActionType, SafetyClass
from .goals import Goal, GoalType
from .state import CityState


@dataclass
class StrategyDecision:
    actions: list[Action]
    rationale: str


class BaselineStrategy:
    """Deterministic, game-version-neutral strategy.

    It proposes only low-risk/read-only intent until the UI adapter and
    verification layer have enough evidence to safely execute changes.
    """

    def decide(self, state: CityState, goals: list[Goal]) -> StrategyDecision:
        if any(g.type == GoalType.AVOID_FAILURE and g.hard for g in goals) and state.warnings:
            return StrategyDecision(
                [Action(ActionType.OBSERVE, safety=SafetyClass.READ_ONLY)],
                "Hard failure-avoidance goal is active; inspect warnings before acting.",
            )
        return StrategyDecision([], "No sufficiently verified baseline action is available.")
