from __future__ import annotations

from dataclasses import dataclass

from .actions import Action, ActionType, SafetyClass
from .calibration import Calibration


@dataclass(frozen=True)
class BudgetControlProfile:
    """Resolution-bound anchors for opening and editing the budget UI."""

    budget_anchor: str = "budget"
    category_anchors: dict[str, str] | None = None

    def anchor_for(self, category: str) -> str:
        normalized = category.strip().lower()
        anchors = self.category_anchors or {}
        if normalized not in anchors:
            raise KeyError(f"No calibrated budget anchor for category '{normalized}'.")
        return anchors[normalized]


class CalibratedBudgetController:
    """Compile budget changes into calibrated clicks without dispatching input."""

    def __init__(self, calibration: Calibration, profile: BudgetControlProfile | None = None):
        self.calibration = calibration
        self.profile = profile or BudgetControlProfile()

    def compile(self, category: str, percentage: int) -> tuple[Action, ...]:
        normalized = category.strip().lower()
        if not normalized:
            raise ValueError("budget category must not be empty")
        if not 0 <= percentage <= 150:
            raise ValueError("budget percentage must be between 0 and 150")
        category_anchor = self.profile.anchor_for(normalized)
        return (
            Action(
                ActionType.CLICK,
                self.calibration.pixel(self.profile.budget_anchor),
                SafetyClass.REVERSIBLE,
                expected_effect="Open the calibrated budget panel.",
            ),
            Action(
                ActionType.CLICK,
                self.calibration.pixel(category_anchor),
                SafetyClass.REVERSIBLE,
                expected_effect=f"Select calibrated budget category '{normalized}'.",
            ),
            Action(
                ActionType.BUDGET,
                (normalized, percentage),
                SafetyClass.REVERSIBLE,
                expected_effect=f"Set {normalized} budget to {percentage}%.",
            ),
        )
