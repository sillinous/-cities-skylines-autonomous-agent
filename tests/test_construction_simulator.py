from cities_agent.actions import Action, ActionType, SafetyClass
from cities_agent.simulator import MockCity


def test_simulator_models_service_budget_and_bulldoze_effects():
    city = MockCity()
    before = city.state

    service = Action(ActionType.SERVICE, ("healthcare",), SafetyClass.REVERSIBLE)
    city.step([service])
    assert city.state.service_coverage["healthcare"] == 25.0
    assert city.state.money < before.money

    budget = Action(ActionType.BUDGET, ("healthcare", 125), SafetyClass.REVERSIBLE)
    city.step([budget])
    assert city.state.budgets["healthcare"] == 125

    money_before = city.state.money
    bulldoze = Action(ActionType.BULLDOZE, ((0.5, 0.5),), SafetyClass.DESTRUCTIVE)
    city.step([bulldoze])
    assert city.state.money > money_before


def test_utility_requires_an_actual_failure():
    city = MockCity()
    action = Action(ActionType.UTILITY, ("power",), SafetyClass.REVERSIBLE)
    assert not city.apply(action)
    city.state.power_ok = False
    assert city.apply(action)
    assert city.state.power_ok is True
