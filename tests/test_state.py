from cities_agent.state import CityState

def test_city_state_serializes():
    state = CityState(money=1000, population=25, traffic_percent=82.5)
    data = state.to_dict()
    assert data["money"] == 1000
    assert data["population"] == 25
    assert data["traffic_percent"] == 82.5
