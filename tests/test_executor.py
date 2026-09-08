from PIL import Image, ImageChops

from cities_agent.actions import Action, ActionResult, ActionType
from cities_agent.executor import PlanExecutor
from cities_agent.planner import Plan, PlanStep
from cities_agent.state import CityState


class FakeObserver:
    def __init__(self):
        self.images = [Image.new("RGB", (64, 36)), Image.new("RGB", (64, 36), 255)]

    def capture(self):
        image = self.images.pop(0) if self.images else Image.new("RGB", (64, 36), 255)
        from cities_agent.perception import Observation
        return Observation(image, image.width, image.height, {})


class FakeController:
    def __init__(self):
        self.stopped = False

    def execute(self, action):
        return ActionResult(action, True, False, "dispatched", 1)

    def emergency_stop(self):
        self.stopped = True


def test_executor_requires_strong_verification():
    controller = FakeController()
    executor = PlanExecutor(controller, FakeObserver(), min_verification_confidence=0.8)
    action = Action(ActionType.CLICK, (10, 10), expected_effect="click")
    plan = Plan([action], "test", steps=[PlanStep(0, action, CityState(), "click")])
    report = executor.execute(plan)
    assert report.completed
    assert report.results[0].verified
    assert not controller.stopped


def test_executor_stops_when_no_effect_is_observed():
    class StaticObserver(FakeObserver):
        def capture(self):
            from cities_agent.perception import Observation
            image = Image.new("RGB", (64, 36))
            return Observation(image, image.width, image.height, {})

    controller = FakeController()
    executor = PlanExecutor(controller, StaticObserver(), min_verification_confidence=0.8)
    action = Action(ActionType.CLICK, (10, 10), expected_effect="click")
    plan = Plan([action], "test", steps=[PlanStep(0, action, CityState(), "click")])
    report = executor.execute(plan)
    assert not report.completed
    assert report.stopped
    assert controller.stopped
