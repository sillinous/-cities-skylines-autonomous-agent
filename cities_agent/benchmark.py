from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Iterable
from .actions import Action
from .simulator import MockCity, SimConfig
from .state import CityState

@dataclass(frozen=True)
class BenchmarkRun:
    strategy: str
    seed: int
    accepted: bool
    score: float
    money_delta: int | None
    population_delta: int | None
    action_count: int
    reason: str

@dataclass(frozen=True)
class BenchmarkSummary:
    strategy: str
    runs: int
    acceptance_rate: float
    mean_score: float
    min_score: float
    max_score: float
    mean_money_delta: float
    mean_population_delta: float
    failures: int

Strategy = Callable[[MockCity], Iterable[Action]]

class StrategyBenchmark:
    """Run deterministic strategies across isolated simulator seeds."""
    def __init__(self, config: SimConfig | None = None): self.config = config or SimConfig()
    def run(self, strategies: dict[str, Strategy], seeds: Iterable[int] = range(5)) -> list[BenchmarkRun]:
        results = []
        for name, strategy in strategies.items():
            for seed in seeds:
                city = MockCity(SimConfig(**{**self.config.__dict__, "starting_money": self.config.starting_money + seed}))
                before: CityState = city.state
                actions = tuple(strategy(city))
                accepted = True; reason = "accepted"
                for action in actions:
                    if not city.apply(action):
                        accepted = False; reason = city.events[-1].reason; break
                    city.wait(1)
                score = self._score(before, city.state)
                md = None if before.money is None or city.state.money is None else city.state.money - before.money
                pd = None if before.population is None or city.state.population is None else city.state.population - before.population
                results.append(BenchmarkRun(name, seed, accepted, score, md, pd, len(actions), reason))
        return results
    @staticmethod
    def summarize(runs: Iterable[BenchmarkRun]) -> list[BenchmarkSummary]:
        grouped: dict[str, list[BenchmarkRun]] = {}
        for run in runs: grouped.setdefault(run.strategy, []).append(run)
        out = []
        for name, items in grouped.items():
            scores = [x.score for x in items]; money = [x.money_delta or 0 for x in items]; pop = [x.population_delta or 0 for x in items]
            out.append(BenchmarkSummary(name, len(items), sum(x.accepted for x in items)/len(items), sum(scores)/len(scores), min(scores), max(scores), sum(money)/len(money), sum(pop)/len(pop), sum(not x.accepted for x in items)))
        return out
    @staticmethod
    def _score(before: CityState, after: CityState) -> float:
        from .evaluator import SimulationEvaluator
        return SimulationEvaluator.score(before, after)
