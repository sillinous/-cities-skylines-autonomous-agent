from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Iterable

from .actions import Action, ActionType
from .state import CityState


@dataclass(frozen=True)
class SimConfig:
    starting_money: int = 50_000
    starting_population: int = 100
    starting_income: int = 1_000
    road_cost: int = 2_000
    utility_cost: int = 5_000
    service_cost: int = 8_000
    zone_cost: int = 500


@dataclass
class SimEvent:
    tick: int
    action: str
    accepted: bool
    reason: str


class MockCity:
    """Small deterministic environment for testing strategy without the game."""

    def __init__(self, config: SimConfig | None = None):
        self.config = config or SimConfig()
        self.tick = 0
        self.state = CityState(
            money=self.config.starting_money,
            population=self.config.starting_population,
            weekly_income=self.config.starting_income,
            residential_demand=50,
            commercial_demand=25,
            industrial_demand=25,
            traffic_percent=100.0,
            power_ok=True,
            water_ok=True,
            sewage_ok=True,
        )
        self.events: list[SimEvent] = []

    def clone(self) -> "MockCity":
        return deepcopy(self)

    def set_state(self, state: CityState) -> None:
        self.state = replace(state, service_coverage=dict(state.service_coverage), confidence=dict(state.confidence))

    def step(self, actions: Iterable[Action] = ()) -> CityState:
        for action in actions:
            self.apply(action)
        self.tick += 1
        self._simulate_time()
        return self._snapshot()

    def wait(self, ticks: int = 1) -> CityState:
        if ticks < 0:
            raise ValueError("ticks must be non-negative")
        for _ in range(ticks):
            self.tick += 1
            self._simulate_time()
        return self._snapshot()

    def _snapshot(self) -> CityState:
        return replace(self.state, service_coverage=dict(self.state.service_coverage), confidence=dict(self.state.confidence))

    def apply(self, action: Action) -> bool:
        accepted = True
        reason = "accepted"
        cost = 0

        if action.type == ActionType.ZONE and action.args:
            zone = str(action.args[0]).lower()
            cost = self.config.zone_cost
            if not self._can_afford(cost):
                accepted, reason = False, "insufficient funds"
            elif zone == "residential":
                self.state.residential_demand = max(0, (self.state.residential_demand or 0) - 10)
                self.state.population = (self.state.population or 0) + 25
            elif zone == "commercial":
                self.state.commercial_demand = max(0, (self.state.commercial_demand or 0) - 10)
            elif zone == "industrial":
                self.state.industrial_demand = max(0, (self.state.industrial_demand or 0) - 10)
            else:
                accepted, reason = False, "unknown zone"
        elif action.type == ActionType.BUILD_ROAD:
            cost = self.config.road_cost
            if not self._can_afford(cost):
                accepted, reason = False, "insufficient funds"
            else:
                self.state.traffic_percent = min(100.0, (self.state.traffic_percent or 0.0) + 8.0)
        elif action.type == ActionType.UTILITY:
            utility = str(action.args[0]).lower() if action.args else ""
            cost = self.config.utility_cost
            if not self._can_afford(cost):
                accepted, reason = False, "insufficient funds"
            elif utility == "power":
                self.state.power_ok = True
            elif utility == "water":
                self.state.water_ok = True
            elif utility == "sewage":
                self.state.sewage_ok = True
            else:
                accepted, reason = False, "unknown utility"
        elif action.type == ActionType.SERVICE:
            service = str(action.args[0]).lower() if action.args else ""
            cost = self.config.service_cost
            if not self._can_afford(cost):
                accepted, reason = False, "insufficient funds"
            elif service:
                coverage = dict(self.state.service_coverage)
                coverage[service] = min(100.0, coverage.get(service, 0.0) + 25.0)
                self.state.service_coverage = coverage
            else:
                accepted, reason = False, "unknown service"
        else:
            accepted, reason = False, "action not implemented by mock"

        if accepted and cost:
            self.state.money = (self.state.money or 0) - cost
        self.events.append(SimEvent(self.tick, action.name, accepted, reason))
        return accepted

    def _can_afford(self, cost: int) -> bool:
        return (self.state.money or 0) >= cost

    def _simulate_time(self) -> None:
        self.state.money = (self.state.money or 0) + (self.state.weekly_income or 0)
        if self.state.population is not None:
            self.state.residential_demand = min(100, (self.state.residential_demand or 0) + 1)
            self.state.traffic_percent = max(0.0, min(100.0, 100.0 - self.state.population / 20.0))
