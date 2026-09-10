from cities_agent.actions import Action, ActionType
from cities_agent.state import CityState
from cities_agent.verification_contracts import ActionSpecificVerifier


def test_zone_contract_rejects_unrelated_demand_change():
    verifier = ActionSpecificVerifier()
    before = CityState(residential_demand=50, commercial_demand=20)
    after = CityState(residential_demand=50, commercial_demand=10)
    action = Action(ActionType.ZONE, expected_effect="Zone residential at target.")
    assert not verifier.verify(before, after, action).success


def test_zone_contract_accepts_target_demand_change():
    verifier = ActionSpecificVerifier()
    before = CityState(residential_demand=50)
    after = CityState(residential_demand=40)
    action = Action(ActionType.ZONE, expected_effect="Zone residential at target.")
    assert verifier.verify(before, after, action).success


def test_service_contract_requires_target_coverage_increase():
    verifier = ActionSpecificVerifier()
    before = CityState(service_coverage={"police": 50.0})
    after = CityState(service_coverage={"police": 60.0, "fire": 90.0})
    action = Action(ActionType.SERVICE, expected_effect="Place service:police at target.")
    assert verifier.verify(before, after, action).success


def test_budget_contract_requires_exact_requested_value():
    verifier = ActionSpecificVerifier()
    before = CityState(budgets={"electricity": 100})
    after = CityState(budgets={"electricity": 125})
    action = Action(ActionType.BUDGET, expected_effect="Set budget electricity to 125%.")
    assert verifier.verify(before, after, action).success


def test_unknown_action_has_no_successful_contract():
    verifier = ActionSpecificVerifier()
    result = verifier.verify(CityState(), CityState(), Action(ActionType.CAMERA, expected_effect="Move camera."))
    assert not result.success
    assert result.confidence == 0.0
