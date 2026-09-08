from PIL import Image

from cities_agent.actions import Action, ActionType
from cities_agent.perception import Observation
from cities_agent.state import CityState
from cities_agent.verification import ActionVerifier


def obs(image):
    return Observation(image, image.width, image.height, {})


def test_state_delta_verifies_zoning_effect():
    before = CityState(residential_demand=60)
    after = CityState(residential_demand=50)
    action = Action(ActionType.ZONE, ("residential",))
    result = ActionVerifier().verify(obs(Image.new("RGB", (100, 100))), obs(Image.new("RGB", (100, 100))), action.name,
                                    before_state=before, after_state=after, action=action)
    assert result.success
    assert result.confidence >= 0.9


def test_unchanged_screen_without_state_effect_is_not_verified():
    image = Image.new("RGB", (100, 100))
    result = ActionVerifier().verify(obs(image), obs(image.copy()), "click")
    assert not result.success


def test_changed_screen_is_only_weakly_verified():
    before = Image.new("RGB", (100, 100), 0)
    after = Image.new("RGB", (100, 100), 255)
    result = ActionVerifier().verify(obs(before), obs(after), "click")
    assert result.success
    assert result.confidence < 0.9
