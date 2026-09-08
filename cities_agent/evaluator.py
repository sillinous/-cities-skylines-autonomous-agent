from __future__ import annotations

from dataclasses import dataclass

from .actions import Action
from .simulator import MockCity
from .state import CityState


@dataclass(frozen=True)
class Evaluation:
    action: Action
    accepted: bool
    score: float
    before: CityState
    after: CityState
    reason: str


class SimulationEvaluator:
    """Evaluate one action in an isolated simulator clone."""

    @staticmethod
    def score(before: CityState, after: CityState) -> float:
        score = 0.0
        if before.population is not None and after.population is not None:
            score += (after.population - before.population) * 2.0
        for field in ("residential_demand", "commercial_demand", "industrial_demand"):
            b, a = getattr(before, field), getattr(after, field)
            if b is not None and a is not None:
                score += max(0, b - a) * 1.5
        if before.traffic_percent is not None and after.traffic_percent is not None:
            score += (after.traffic_percent - before.traffic_percent) * 0.5
        if before.money is not None and after.money is not None:
            score += max(-1000, min(1000, after.money - before.money)) * 0.01
        failures_before = sum(x is False for x in (before.power_ok, before.water_ok, before.sewage_ok))
        failures_after = sum(x is False for x in (after.power_ok, after.water_ok, after.sewage_ok))
        score += (failures_before - failures_after) * 100.0
        return score

    def evaluate(self, city: MockCity, action: Action) -> Evaluation:
        trial = city.clone()
        before = trial.state
        accepted = trial.step([action])
        event = trial.events[-1]
        if not event.accepted:
            return Evaluation(action, False, float("-inf"), before, accepted, event.reason)
        return Evaluation(action, True, self.score(before, accepted), before, accepted, event.reason)
