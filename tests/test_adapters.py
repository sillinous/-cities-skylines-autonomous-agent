from cities_agent.actions import Action, ActionResult, ActionType
from cities_agent.adapters import CitiesSkylinesAdapter
from cities_agent.calibration import CalibrationError, calibrate
from cities_agent.perception import Observation
from cities_agent.state import CityState
from PIL import Image


class FakeSensor:
    def __init__(self):
        self.observation = Observation(Image.new("RGB", (1920, 1080)), 1920, 1080, {})

    def observe(self):
        return self.observation

    def read_state(self, observation):
        return CityState(money=1234, confidence={"money": 0.99})


class FakeController:
    def __init__(self):
        self.actions = []
        self.stopped = False

    def execute(self, action):
        self.actions.append(action)
        return ActionResult(action, True, True, "verified", 1)

    def emergency_stop(self):
        self.stopped = True


def test_adapter_composes_sensor_and_controller():
    sensor = FakeSensor()
    controller = FakeController()
    adapter = CitiesSkylinesAdapter(sensor, controller)
    observation, state = adapter.observe()
    assert observation.width == 1920
    assert state.money == 1234
    action = Action(ActionType.OBSERVE)
    assert adapter.execute(action).verified
    adapter.emergency_stop()
    assert controller.stopped


def test_normalized_calibration_converts_to_pixels():
    calibration = calibrate(FakeSensor().observation, {"center": (0.5, 0.5)})
    assert calibration.pixel("center") == (960, 540)


def test_calibration_rejects_invalid_anchor():
    try:
        calibrate(FakeSensor().observation, {"bad": (1.1, 0.5)})
    except CalibrationError:
        return
    assert False, "Expected CalibrationError"
