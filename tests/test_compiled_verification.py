from PIL import Image

from cities_agent.actions import ActionType
from cities_agent.budget_control import BudgetControlProfile
from cities_agent.calibration import Calibration
from cities_agent.compiler import IntentCompiler
from cities_agent.intent import Intent, IntentKind
from cities_agent.state import CityState
from cities_agent.verification_contracts import ActionSpecificVerifier
from cities_agent.live_verification import LiveSemanticVerifier
from cities_agent.perception import Observation


def calibration():
    return Calibration(1000, 500, {
        "zone:residential": (0.1, 0.1),
        "utility:power": (0.2, 0.1),
        "service:police": (0.3, 0.1),
        "road:road": (0.4, 0.1),
        "bulldoze": (0.5, 0.1),
        "budget": (0.9, 0.1),
        "budget:electricity": (0.8, 0.2),
        "budget:slider_start": (0.5, 0.2),
        "budget:slider_end": (0.7, 0.2),
    })


def test_zone_final_click_is_semantically_tagged():
    result = IntentCompiler(calibration()).compile(Intent(IntentKind.ZONE, target="residential", point=(0.6, 0.6)))
    assert [a.type for a in result.actions] == [ActionType.CLICK, ActionType.CLICK]
    assert result.actions[0].meta("phase") == "tool"
    assert result.actions[1].meta("phase") == "effect"
    assert result.actions[1].meta("semantic_kind") == "zone"


def test_zone_contract_rejects_unrelated_demand_change():
    action = IntentCompiler(calibration()).compile(Intent(IntentKind.ZONE, target="residential", point=(0.6, 0.6))).actions[-1]
    before = CityState(residential_demand=50, commercial_demand=20)
    after = CityState(residential_demand=50, commercial_demand=10)
    assert not ActionSpecificVerifier().verify(before, after, action).success


def test_zone_contract_accepts_target_demand_change():
    action = IntentCompiler(calibration()).compile(Intent(IntentKind.ZONE, target="residential", point=(0.6, 0.6))).actions[-1]
    before = CityState(residential_demand=50, commercial_demand=20)
    after = CityState(residential_demand=40, commercial_demand=20)
    assert ActionSpecificVerifier().verify(before, after, action).success


def test_service_final_click_requires_target_coverage_increase():
    action = IntentCompiler(calibration()).compile(Intent(IntentKind.SERVICE, target="police", point=(0.6, 0.6))).actions[-1]
    before = CityState(service_coverage={"police": 40.0})
    after = CityState(service_coverage={"police": 40.0, "fire": 90.0})
    assert not ActionSpecificVerifier().verify(before, after, action).success
    after = CityState(service_coverage={"police": 55.0})
    assert ActionSpecificVerifier().verify(before, after, action).success


def test_budget_final_click_requires_exact_category_and_value():
    profile = BudgetControlProfile(category_anchors={"electricity": "budget:electricity"})
    action = IntentCompiler(calibration(), budget_profile=profile).compile(Intent(IntentKind.BUDGET, target="electricity", value=125)).actions[-1]
    assert action.type == ActionType.CLICK
    before = CityState(budgets={"electricity": 100})
    after = CityState(budgets={"electricity": 125})
    assert ActionSpecificVerifier().verify(before, after, action).success
    wrong = CityState(budgets={"electricity": 120})
    assert not ActionSpecificVerifier().verify(before, wrong, action).success


def test_intermediate_tool_click_cannot_fall_through_to_screen_change():
    action = IntentCompiler(calibration()).compile(Intent(IntentKind.ZONE, target="residential", point=(0.6, 0.6))).actions[0]
    before = CityState(residential_demand=50)
    after = CityState(residential_demand=40)
    image = Image.new("RGB", (2, 2))
    observation = Observation(screenshot=image, width=2, height=2)
    verified = LiveSemanticVerifier().verify(observation, observation, action.name, before_state=before, after_state=after, action=action)
    assert not verified.success
