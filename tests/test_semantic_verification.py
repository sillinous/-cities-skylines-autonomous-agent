from cities_agent.actions import Action, ActionType
from cities_agent.semantic_verification import SemanticVerificationEngine, default_semantic_rules
from cities_agent.state import CityState


def test_demand_delta_is_high_confidence_semantic_evidence():
    engine = SemanticVerificationEngine(default_semantic_rules())
    before = CityState(residential_demand=50)
    after = CityState(residential_demand=40)
    result = engine.verify(before, after, Action(ActionType.ZONE, expected_effect="Increase residential capacity."))
    assert result.success
    assert result.confidence >= 0.9


def test_unchanged_state_does_not_verify():
    engine = SemanticVerificationEngine(default_semantic_rules())
    state = CityState(residential_demand=50)
    result = engine.verify(state, state, Action(ActionType.ZONE, expected_effect="Increase residential capacity."))
    assert not result.success
    assert result.confidence == 0.0


def test_utility_recovery_is_semantic_evidence():
    engine = SemanticVerificationEngine(default_semantic_rules())
    before = CityState(power_ok=False)
    after = CityState(power_ok=True)
    result = engine.verify(before, after, Action(ActionType.UTILITY, expected_effect="Restore power."))
    assert result.success
