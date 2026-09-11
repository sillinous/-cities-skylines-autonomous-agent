from PIL import Image

from cities_agent.actions import Action, ActionResult, ActionType, SafetyClass
from cities_agent.budget_control import BudgetControlProfile
from cities_agent.calibration import Calibration
from cities_agent.intent import Intent, IntentKind
from cities_agent.live import LivePilot
from cities_agent.perception import Observation
from cities_agent.pilot import PilotConfig, PilotGuard
from cities_agent.state import CityState
from cities_agent.verification import VerificationResult


class FakeObserver:
    def __init__(self):
        self.calls = 0

    def capture(self):
        self.calls += 1
        return Observation(Image.new("RGB", (1920, 1080)), 1920, 1080)


class FakeController:
    def __init__(self):
        self.actions = []
        self.stopped = False

    def execute(self, action):
        self.actions.append(action)
        return ActionResult(action, True, False, "dispatched", 1)

    def emergency_stop(self):
        self.stopped = True


class FakeVerifier:
    def verify(self, *args, **kwargs):
        return VerificationResult(True, "semantic state delta verified", 0.95)


def live_config():
    return PilotConfig(dry_run=False, allow_input=True, allow_reversible=True)


def test_live_pilot_defaults_to_dry_run_gate():
    observer = FakeObserver()
    controller = FakeController()
    guard = PilotGuard(PilotConfig(dry_run=True))
    pilot = LivePilot(
        observer=observer,
        state_reader=lambda _: CityState(simulation_paused=True),
        intent_provider=lambda *_: Intent(IntentKind.CAMERA, point=(0.5, 0.5)),
        controller=controller,
        pilot=guard,
    )
    obs = observer.capture()
    pilot.set_calibration(Calibration(1920, 1080, {"center": (0.5, 0.5)}), obs)
    result = pilot.run_once()
    assert result.halted
    assert controller.actions == []
    assert controller.stopped


def test_live_pilot_verifies_dispatched_action():
    observer = FakeObserver()
    controller = FakeController()
    guard = PilotGuard(live_config(), game_detector=lambda _observation: True, foreground_checker=lambda: True)
    pilot = LivePilot(
        observer=observer,
        state_reader=lambda _: CityState(simulation_paused=True),
        intent_provider=lambda *_: Intent(IntentKind.CAMERA, point=(0.5, 0.5)),
        controller=controller,
        pilot=guard,
        verifier=FakeVerifier(),
    )
    obs = observer.capture()
    pilot.set_calibration(Calibration(1920, 1080, {"center": (0.5, 0.5)}), obs)
    result = pilot.run_once()
    assert not result.halted
    assert len(controller.actions) == 1
    assert result.verification[0].success


def test_live_pilot_preserves_unexecuted_compiled_actions():
    observer = FakeObserver()
    controller = FakeController()
    guard = PilotGuard(live_config(), game_detector=lambda _observation: True, foreground_checker=lambda: True)
    pilot = LivePilot(
        observer=observer,
        state_reader=lambda _: CityState(simulation_paused=True),
        intent_provider=lambda *_: Intent(IntentKind.BUDGET, target="electricity", value=75),
        controller=controller,
        pilot=guard,
        verifier=FakeVerifier(),
    )
    obs = observer.capture()
    calibration = Calibration(1920, 1080, {
        "budget": (0.9, 0.1),
        "budget:electricity": (0.8, 0.2),
        "budget:slider_start": (0.5, 0.2),
        "budget:slider_end": (0.7, 0.2),
    })
    pilot.set_calibration(calibration, obs)
    pilot.compiler = __import__("cities_agent.compiler", fromlist=["IntentCompiler"]).IntentCompiler(
        calibration,
        budget_profile=BudgetControlProfile(category_anchors={"electricity": "budget:electricity"}),
    )
    first = pilot.run_once(max_actions=1)
    assert len(first.actions) == 1
    assert len(pilot.pending_actions) == 2
    second = pilot.run_once(max_actions=1)
    assert len(second.actions) == 1
    assert len(pilot.pending_actions) == 1
    assert len(controller.actions) == 2


def test_live_pilot_rejects_reversible_input_without_explicit_policy():
    observer = FakeObserver()
    guard = PilotGuard(PilotConfig(dry_run=False), game_detector=lambda _observation: True, foreground_checker=lambda: True)
    obs = observer.capture()
    guard.set_calibration(Calibration(1920, 1080, {"center": (0.5, 0.5)}), obs)
    result = guard.authorize(
        Action(ActionType.CLICK, (10, 10), SafetyClass.REVERSIBLE),
        obs,
        state=CityState(simulation_paused=True),
    )
    assert not result.ready
    assert "policy" in result.reason.lower()
