from cities_agent.actions import Action, ActionType
from cities_agent.simulator import MockCity, SimConfig


def test_mock_city_is_deterministic_and_advances():
    city = MockCity(SimConfig(starting_money=1000, starting_population=100))
    before = city.state.money
    after = city.step([Action(ActionType.ZONE, ("residential",))])

    assert after.population == 125
    assert after.money == before + 1000
    assert city.tick == 1
    assert city.events[-1].accepted is True


def test_mock_rejects_unknown_action_without_faking_effect():
    city = MockCity()
    before = city.state.to_dict()
    assert city.apply(Action(ActionType.BUILD_ROAD, (1, 2, 3, 4))) is False
    assert city.state.to_dict() == before
    assert city.events[-1].reason == "action not implemented by mock"
