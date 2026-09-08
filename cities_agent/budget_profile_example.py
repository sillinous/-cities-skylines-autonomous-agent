"""Example calibration shape; values must be measured for the user's game window."""

from .budget_control import BudgetControlProfile

EXAMPLE_BUDGET_PROFILE = BudgetControlProfile(
    budget_anchor="budget",
    category_anchors={
        "electricity": "budget:electricity",
        "water": "budget:water",
        "healthcare": "budget:healthcare",
        "police": "budget:police",
        "fire": "budget:fire",
    },
    slider_start_anchor="budget:slider_start",
    slider_end_anchor="budget:slider_end",
)
