from dataclasses import dataclass
from enum import Enum
from typing import Any


class GoalType(str, Enum):
    GROW_POPULATION = "grow_population"
    MAINTAIN_BUDGET = "maintain_budget"
    IMPROVE_TRAFFIC = "improve_traffic"
    FIX_UTILITY = "fix_utility"
    SATISFY_DEMAND = "satisfy_demand"
    AVOID_FAILURE = "avoid_failure"
    CUSTOM = "custom"


@dataclass(frozen=True)
class Goal:
    type: GoalType
    target: Any = None
    priority: int = 50
    hard: bool = False
    risk_tolerance: float = 0.0
    description: str = ""

    def __post_init__(self):
        if not 0 <= self.priority <= 100:
            raise ValueError("priority must be between 0 and 100")
        if not 0.0 <= self.risk_tolerance <= 1.0:
            raise ValueError("risk_tolerance must be between 0 and 1")
