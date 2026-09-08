from cities_agent.actions import Action, ActionType
from cities_agent.simulator import MockCity, SimConfig


def test_mock_city_is_deterministic_and_advances():
    city = MockCity(SimConfig(starting_money=1000, starting_population=250))
    before = city.state.money
    after = city.step([Action(ActionType.ZONE, ("residential",))])

    assert after.population == 275
    assert after.money == before + 1000 - 500
    assert city.tick == 1
    assert city.events[-1].accepted is True


def test_mock_rejects_unknown_zone_without_faking_effect():
    city = MockCity()
    before = city.state.to_dict()
    assert city.apply(Action(ActionType.ZONE, ("not-a-zone",))) is False
    assert city.state.to_dict() == before
    assert city.events[-1].reason == "unknown zone"


def test_mock_wait_advances_time_without_action():
    city = MockCity(SimConfig(starting_money=1000, starting_income=250))
    city.wait(2)
    assert city.tick == 2
    assert city.state.money == 1500
