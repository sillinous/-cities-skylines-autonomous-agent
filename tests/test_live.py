from PIL import Image

from cities_agent.actions import ActionResult
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


def test_live_pilot_defaults_to_dry_run_gate():
    observer = FakeObserver()
    controller = FakeController()
    guard = PilotGuard(PilotConfig(dry_run=True))
    obs = observer.capture()
    guard.set_calibration(Calibration(1920, 1080, {"center": (0.5, 0.5)}), obs)
    pilot = LivePilot(
        observer=observer,
        state_reader=lambda _: CityState(simulation_paused=True),
        intent_provider=lambda *_: Intent(IntentKind.CAMERA, point=(0.5, 0.5)),
        controller=controller,
        pilot=guard,
    )
    result = pilot.run_once()
    assert result.halted
    assert controller.actions == []
    assert controller.stopped


def test_live_pilot_verifies_dispatched_action():
    observer = FakeObserver()
    controller = FakeController()
    guard = PilotGuard(PilotConfig(dry_run=False))
    obs = observer.capture()
    guard.set_calibration(Calibration(1920, 1080, {"center": (0.5, 0.5)}), obs)
    pilot = LivePilot(
        observer=observer,
        state_reader=lambda _: CityState(simulation_paused=True),
        intent_provider=lambda *_: Intent(IntentKind.CAMERA, point=(0.5, 0.5)),
        controller=controller,
        pilot=guard,
        verifier=FakeVerifier(),
    )
    result = pilot.run_once()
    assert not result.halted
    assert len(controller.actions) == 1
    assert result.verification[0].success
