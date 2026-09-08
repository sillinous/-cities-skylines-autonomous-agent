import pytest

from cities_agent.actions import ActionType, SafetyClass
from cities_agent.budget_control import BudgetControlProfile, CalibratedBudgetController
from cities_agent.calibration import Calibration


@pytest.fixture
def controller():
    calibration = Calibration(1000, 500, {
        "budget": (0.9, 0.1),
        "budget:electricity": (0.8, 0.2),
        "budget:slider_start": (0.5, 0.2),
        "budget:slider_end": (0.7, 0.2),
    })
    profile = BudgetControlProfile(
        budget_anchor="budget",
        category_anchors={"electricity": "budget:electricity"},
    )
    return CalibratedBudgetController(calibration, profile)


def test_budget_compiles_to_calibrated_steps(controller):
    actions = controller.compile("electricity", 75)
    assert [a.type for a in actions] == [ActionType.CLICK, ActionType.CLICK, ActionType.CLICK]
    assert actions[0].args == (900, 50)
    assert actions[1].args == (800, 100)
    assert actions[2].args == (600, 100)
    assert all(a.safety == SafetyClass.REVERSIBLE for a in actions)


def test_unknown_budget_category_is_rejected(controller):
    with pytest.raises(KeyError, match="No calibrated budget anchor"):
        controller.compile("police", 100)


def test_budget_range_is_validated(controller):
    with pytest.raises(ValueError, match="between 0 and 150"):
        controller.compile("electricity", 151)
