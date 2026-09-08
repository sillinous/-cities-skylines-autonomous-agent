from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

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


@dataclass(frozen=True)
class SequenceEvaluation:
    actions: tuple[Action, ...]
    accepted: bool
    score: float
    before: CityState
    after: CityState
    reason: str
    failed_index: int | None = None


class SimulationEvaluator:
    """Evaluate actions and short action sequences in isolated simulator clones."""

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
        after = trial.step([action])
        event = trial.events[-1]
        if not event.accepted:
            return Evaluation(action, False, float("-inf"), before, after, event.reason)
        return Evaluation(action, True, self.score(before, after), before, after, event.reason)

    def evaluate_sequence(
        self,
        city: MockCity,
        actions: Sequence[Action],
        *,
        step_penalty: float = 0.25,
    ) -> SequenceEvaluation:
        """Evaluate a complete sequence; one failed step invalidates the sequence."""
        trial = city.clone()
        before = trial.state
        incremental = 0.0
        for index, action in enumerate(actions):
            previous = trial.state
            after = trial.step([action])
            event = trial.events[-1]
            if not event.accepted:
                return SequenceEvaluation(
                    tuple(actions), False, float("-inf"), before, after,
                    f"step {index} failed: {event.reason}", index,
                )
            incremental += self.score(previous, after)
        final_score = self.score(before, trial.state) + 0.25 * incremental - step_penalty * len(actions)
        return SequenceEvaluation(tuple(actions), True, final_score, before, trial.state, "accepted")
