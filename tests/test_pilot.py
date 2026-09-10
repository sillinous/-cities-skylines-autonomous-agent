from cities_agent.actions import Action, ActionType, SafetyClass
from cities_agent.calibration import Calibration
from cities_agent.perception import Observation
from cities_agent.pilot import DryRunController, PilotConfig, PilotGuard
from cities_agent.state import CityState
from PIL import Image


def observation(width=1920, height=1080):
    image = Image.new("RGB", (width, height))
    return Observation(image, width, height)


def calibrated_guard(**kwargs):
    guard = PilotGuard(
        PilotConfig(**kwargs),
        game_detector=lambda _observation: True,
        foreground_checker=lambda: True,
    )
    obs = observation()
    guard.set_calibration(Calibration(1920, 1080, {"center": (0.5, 0.5)}), obs)
    return guard, obs


def test_dry_run_blocks_real_input():
    guard, obs = calibrated_guard(dry_run=True)
    action = Action(ActionType.CLICK, (10, 10), SafetyClass.REVERSIBLE)
    result = guard.authorize(action, obs, state=CityState(simulation_paused=True))
    assert not result.ready
    assert "Dry-run" in result.reason


def test_pilot_requires_pause():
    guard, obs = calibrated_guard(dry_run=False, require_paused=True)
    action = Action(ActionType.CLICK, (10, 10), SafetyClass.REVERSIBLE)
    result = guard.authorize(action, obs, state=CityState(simulation_paused=False))
    assert not result.ready
    assert "paused" in result.reason


def test_pilot_requires_foreground():
    guard, obs = calibrated_guard(dry_run=False, require_foreground=True)
    guard.foreground_checker = lambda: False
    action = Action(ActionType.CLICK, (10, 10), SafetyClass.REVERSIBLE)
    result = guard.authorize(action, obs, state=CityState(simulation_paused=True))
    assert not result.ready
    assert "foreground" in result.reason


def test_pilot_rejects_game_not_detected():
    guard, obs = calibrated_guard(dry_run=False)
    guard.game_detector = lambda observation: False
    action = Action(ActionType.CLICK, (10, 10), SafetyClass.REVERSIBLE)
    result = guard.authorize(action, obs, state=CityState(simulation_paused=True))
    assert not result.ready
    assert "not detected" in result.reason


def test_live_mode_defaults_to_real_window_checks():
    guard = PilotGuard(PilotConfig(dry_run=False))
    assert guard.game_detector.__self__ is guard.game_window
    assert guard.foreground_checker.__self__ is guard.game_window


def test_pilot_allows_read_only_without_real_input():
    guard = PilotGuard()
    action = Action(ActionType.OBSERVE)
    result = guard.authorize(action, observation())
    assert result.ready


def test_dry_run_controller_never_executes():
    controller = DryRunController()
    action = Action(ActionType.KEY, ("space",), SafetyClass.REVERSIBLE)
    result = controller.execute(action)
    assert not result.executed
    assert not result.verified
    assert controller.actions == [action]
