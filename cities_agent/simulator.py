from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from .actions import Action, ActionType
from .state import CityState


@dataclass(frozen=True)
class SimConfig:
    starting_money: int = 50_000
    starting_population: int = 100
    starting_income: int = 1_000


@dataclass
class SimEvent:
    tick: int
    action: str
    accepted: bool
    reason: str


class MockCity:
    """Small deterministic environment for testing strategy without the game."""

    def __init__(self, config: SimConfig | None = None):
        cfg = config or SimConfig()
        self.tick = 0
        self.state = CityState(
            money=cfg.starting_money,
            population=cfg.starting_population,
            weekly_income=cfg.starting_income,
            residential_demand=50,
            commercial_demand=25,
            industrial_demand=25,
            traffic_percent=100.0,
            power_ok=True,
            water_ok=True,
            sewage_ok=True,
        )
        self.events: list[SimEvent] = []

    def step(self, actions: Iterable[Action] = ()) -> CityState:
        for action in actions:
            self.apply(action)
        self.tick += 1
        self._simulate_time()
        return replace(self.state)

    def apply(self, action: Action) -> bool:
        accepted = True
        reason = "accepted"
        if action.type == ActionType.ZONE and action.args:
            zone = str(action.args[0]).lower()
            if zone == "residential":
                self.state.residential_demand = max(0, (self.state.residential_demand or 0) - 10)
                self.state.population = (self.state.population or 0) + 25
            elif zone == "commercial":
                self.state.commercial_demand = max(0, (self.state.commercial_demand or 0) - 10)
            elif zone == "industrial":
                self.state.industrial_demand = max(0, (self.state.industrial_demand or 0) - 10)
            else:
                accepted, reason = False, "unknown zone"
        else:
            accepted, reason = False, "action not implemented by mock"
        self.events.append(SimEvent(self.tick, action.name, accepted, reason))
        return accepted

    def _simulate_time(self) -> None:
        self.state.money = (self.state.money or 0) + (self.state.weekly_income or 0)
        if self.state.population is not None:
            self.state.residential_demand = min(100, (self.state.residential_demand or 0) + 1)
            self.state.traffic_percent = max(0.0, min(100.0, 100.0 - self.state.population / 20.0))
