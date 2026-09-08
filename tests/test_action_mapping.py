import pytest

from cities_agent.action_mapping import CitiesSkylinesActionMapper
from cities_agent.actions import ActionType, SafetyClass
from cities_agent.calibration import Calibration


@pytest.fixture
def mapper():
    return CitiesSkylinesActionMapper(Calibration(1000, 500, {
        "utility:power": (0.1, 0.1),
        "service:police": (0.2, 0.1),
        "zone:residential": (0.3, 0.1),
        "bulldoze": (0.4, 0.1),
    }))


def test_utility_requires_and_maps_target(mapper):
    actions = mapper.utility("power", (0.6, 0.8))
    assert actions[0].type == ActionType.CLICK
    assert actions[1].type == ActionType.CLICK
    assert actions[1].args == (600, 400)


def test_service_requires_and_maps_target(mapper):
    actions = mapper.service("police", (0.4, 0.5))
    assert actions[0].type == ActionType.CLICK
    assert actions[1].args == (400, 250)


def test_utility_without_target_is_rejected(mapper):
    with pytest.raises(ValueError, match="requires point"):
        mapper.utility("power")


def test_service_without_target_is_rejected(mapper):
    with pytest.raises(ValueError, match="requires point"):
        mapper.service("police")


def test_bulldoze_remains_destructive(mapper):
    actions = mapper.bulldoze((0.5, 0.5))
    assert actions[-1].safety == SafetyClass.DESTRUCTIVE
