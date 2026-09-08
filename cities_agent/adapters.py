from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .actions import Action, ActionResult
from .perception import Observation
from .state import CityState


class GameSensor(Protocol):
    """Game-facing read interface. Implementations must not mutate the game."""

    def observe(self) -> Observation: ...

    def read_state(self, observation: Observation) -> CityState: ...


class GameController(Protocol):
    """Game-facing write interface behind the safety controller."""

    def execute(self, action: Action) -> ActionResult: ...

    def emergency_stop(self) -> None: ...


@dataclass(frozen=True)
class AdapterStatus:
    game_detected: bool
    resolution: tuple[int, int] | None = None
    message: str = ""


class CitiesSkylinesAdapter:
    """Composition point for a future Cities: Skylines-specific UI adapter.

    The adapter intentionally does not guess UI coordinates. A concrete
    implementation can supply calibrated perception and controller objects.
    """

    def __init__(self, sensor: GameSensor, controller: GameController):
        self.sensor = sensor
        self.controller = controller

    def observe(self) -> tuple[Observation, CityState]:
        observation = self.sensor.observe()
        return observation, self.sensor.read_state(observation)

    def execute(self, action: Action) -> ActionResult:
        return self.controller.execute(action)

    def emergency_stop(self) -> None:
        self.controller.emergency_stop()
