from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .actions import Action, ActionResult, SafetyClass
from .calibration import Calibration, CalibrationError
from .perception import Observation


@dataclass(frozen=True)
class PreflightResult:
    ready: bool
    reason: str


@dataclass(frozen=True)
class PilotConfig:
    """Explicit gates for real-game input.

    Real input requires all gates to be true. Dry-run remains the default.
    """

    dry_run: bool = True
    require_game_detected: bool = True
    require_foreground: bool = True
    require_calibration: bool = True
    require_paused: bool = True


class PilotGuard:
    """Safety boundary between planning and real OS input."""

    def __init__(
        self,
        config: PilotConfig | None = None,
        *,
        game_detector: Callable[[Observation], bool] | None = None,
        foreground_checker: Callable[[], bool] | None = None,
    ):
        self.config = config or PilotConfig()
        self.game_detector = game_detector or (lambda observation: True)
        self.foreground_checker = foreground_checker or (lambda: True)
        self.calibration: Calibration | None = None
        self.halted = False
        self.actions_this_cycle = 0

    def reset_cycle(self) -> None:
        self.actions_this_cycle = 0

    def halt(self) -> None:
        self.halted = True

    def clear_halt(self) -> None:
        self.halted = False

    def set_calibration(self, calibration: Calibration, observation: Observation) -> None:
        if (calibration.width, calibration.height) != (observation.width, observation.height):
            raise CalibrationError("Calibration resolution does not match the observation.")
        self.calibration = calibration

    def preflight(self, observation: Observation, *, state=None, max_actions: int = 1) -> PreflightResult:
        if self.halted:
            return PreflightResult(False, "Pilot guard is halted.")
        if max_actions < 1:
            return PreflightResult(False, "Action budget must be positive.")
        if self.actions_this_cycle >= max_actions:
            return PreflightResult(False, "Per-cycle action budget exhausted.")
        if self.config.require_game_detected and not self.game_detector(observation):
            return PreflightResult(False, "Cities: Skylines game window was not detected.")
        if self.config.require_foreground and not self.foreground_checker():
            return PreflightResult(False, "Cities: Skylines is not the foreground application.")
        if self.config.require_calibration and self.calibration is None:
            return PreflightResult(False, "Pilot calibration is not established.")
        if self.config.require_paused and state is not None and state.simulation_paused is False:
            return PreflightResult(False, "Simulation must be paused before pilot input.")
        return PreflightResult(True, "Pilot preflight passed.")

    def authorize(self, action: Action, observation: Observation, *, state=None, max_actions: int = 1) -> PreflightResult:
        if action.safety == SafetyClass.READ_ONLY:
            return PreflightResult(True, "Read-only action does not require pilot input.")
        result = self.preflight(observation, state=state, max_actions=max_actions)
        if not result.ready:
            return result
        if self.config.dry_run:
            return PreflightResult(False, "Dry-run mode: real input is intentionally disabled.")
        return result

    def record_dispatch(self) -> None:
        self.actions_this_cycle += 1


class DryRunController:
    """Controller-compatible sink that never calls pyautogui."""

    def __init__(self):
        self.stopped = False
        self.actions: list[Action] = []

    def emergency_stop(self) -> None:
        self.stopped = True

    def execute(self, action: Action) -> ActionResult:
        if self.stopped:
            return ActionResult(action, False, False, "Dry-run controller is stopped.")
        self.actions.append(action)
        return ActionResult(
            action,
            executed=False,
            verified=False,
            reason="Dry-run: input was not dispatched.",
            attempts=0,
            metadata={"dry_run": True},
        )
