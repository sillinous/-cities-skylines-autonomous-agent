from cities_agent.actions import Action, ActionType, SafetyClass
from cities_agent.evaluator import SimulationEvaluator
from cities_agent.simulator import MockCity, SimConfig


def test_evaluator_scores_residential_growth_positive():
    city = MockCity(SimConfig(starting_money=10_000))
    action = Action(ActionType.ZONE, ("residential",), SafetyClass.REVERSIBLE)
    result = SimulationEvaluator().evaluate(city, action)
    assert result.accepted is True
    assert result.score > 0
    assert result.after.population > result.before.population


def test_evaluator_rejects_unaffordable_construction():
    city = MockCity(SimConfig(starting_money=100))
    action = Action(ActionType.BUILD_ROAD, (), SafetyClass.REVERSIBLE)
    result = SimulationEvaluator().evaluate(city, action)
    assert result.accepted is False
    assert result.score == float("-inf")


def test_utility_repair_improves_failure_score():
    city = MockCity()
    city.state.power_ok = False
    action = Action(ActionType.UTILITY, ("power",), SafetyClass.REVERSIBLE)
    result = SimulationEvaluator().evaluate(city, action)
    assert result.accepted is True
    assert result.after.power_ok is True
    assert result.score > 0
