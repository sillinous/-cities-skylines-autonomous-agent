from cities_agent.budget_control import BudgetControlProfile
from cities_agent.calibration import Calibration
from cities_agent.compiler import IntentCompiler
from cities_agent.intent import Intent, IntentKind


def test_compiler_rejects_unprofiled_budget_category():
    compiler = IntentCompiler(
        Calibration(1000, 500, {
            "budget": (0.9, 0.1),
            "budget:electricity": (0.8, 0.2),
            "budget:slider_start": (0.5, 0.2),
            "budget:slider_end": (0.7, 0.2),
        }),
        budget_profile=BudgetControlProfile(
            category_anchors={"electricity": "budget:electricity"},
            slider_start_anchor="budget:slider_start",
            slider_end_anchor="budget:slider_end",
        ),
    )
    result = compiler.compile(Intent(IntentKind.BUDGET, target="police", value=100))
    assert not result.actions
    assert "No calibrated budget anchor" in result.reason
