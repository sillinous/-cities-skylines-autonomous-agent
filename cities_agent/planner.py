from __future__ import annotations

from dataclasses import dataclass, field

from .actions import Action
from .perception import Observation
from .state import CityState
from .strategic_manager import Candidate, StrategicManager
from .simulator import MockCity


@dataclass(frozen=True)
class PlanStep:
    index: int
    action: Action
    expected_state: CityState
    rationale: str
    max_retries: int = 0


@dataclass
class Plan:
    actions: list[Action]
    rationale: str
    candidates: list[Candidate] = field(default_factory=list)
    steps: list[PlanStep] = field(default_factory=list)
    score: float = 0.0
    valid: bool = True


class MultiStepPlanner:
    """Bounded look-ahead planner with simulation-first evaluation."""

    def __init__(self, manager: StrategicManager | None = None, max_depth: int = 3, branch_limit: int = 4):
        self.manager = manager or StrategicManager()
        self.max_depth = max(1, max_depth)
        self.branch_limit = max(1, branch_limit)

    def search(self, state: CityState, simulator: MockCity | None = None) -> Plan:
        city = simulator.clone() if simulator else MockCity()
        city.set_state(state)
        goals = self.manager.goals_for(state)
        if goals and goals[0].hard:
            return Plan([], "Hard safety condition requires observation and recovery before planning.", valid=False)

        best: tuple[float, tuple[Action, ...]] | None = None
        frontier: list[tuple[tuple[Action, ...], MockCity]] = [((), city)]
        for _depth in range(1, self.max_depth + 1):
            next_frontier: list[tuple[tuple[Action, ...], MockCity]] = []
            for actions, node in frontier:
                for action in self._authorized_candidates(node.state)[: self.branch_limit]:
                    child = node.clone()
                    before = child.state
                    after = child.step([action])
                    if not child.events[-1].accepted:
                        continue
                    sequence = actions + (action,)
                    value = self.manager.evaluator.score(state, after)
                    value += 0.25 * self.manager.evaluator.score(before, after)
                    value -= 0.5 * len(sequence)
                    if best is None or value > best[0]:
                        best = (value, sequence)
                    next_frontier.append((sequence, child))
            frontier = next_frontier
            if not frontier:
                break

        if best is None or best[0] <= 0:
            return Plan([], "No safe positive-value sequence was found by bounded simulation.", valid=False)

        score, actions = best
        steps = self._make_steps(state, actions, simulator)
        rationale = f"Selected a {len(actions)}-step simulated sequence with expected value {score:.2f}."
        self.manager.audit.record("plan_created", rationale, depth=len(actions), score=score)
        return Plan(list(actions), rationale, steps=steps, score=score)

    def replan(self, observed_state: CityState, previous: Plan | None = None, simulator: MockCity | None = None) -> Plan:
        if previous is not None:
            self.manager.audit.record("replan", "Observed state changed; invalidating remaining plan.", previous_steps=len(previous.steps))
        return self.search(observed_state, simulator)

    def validate_step(self, step: PlanStep, observed_state: CityState, tolerance: float = 0.0) -> bool:
        for name in ("money", "population", "residential_demand", "commercial_demand", "industrial_demand"):
            expected = getattr(step.expected_state, name)
            actual = getattr(observed_state, name)
            if expected is not None and actual is not None and abs(actual - expected) > tolerance:
                self.manager.audit.record("plan_invalidated", f"Step {step.index} diverged on {name}.", expected=expected, actual=actual)
                return False
        for name in ("power_ok", "water_ok", "sewage_ok"):
            expected = getattr(step.expected_state, name)
            actual = getattr(observed_state, name)
            if expected is not None and actual is not None and expected != actual:
                self.manager.audit.record("plan_invalidated", f"Step {step.index} diverged on {name}.", expected=expected, actual=actual)
                return False
        return True

    def _authorized_candidates(self, state: CityState) -> list[Action]:
        result = []
        for action in self.manager.candidates(state):
            authorized, reason = self.manager.policy.authorize(action)
            if authorized:
                result.append(action)
            else:
                self.manager.audit.record("candidate_blocked", reason, action=action.name)
        return result

    def _make_steps(self, state: CityState, actions: tuple[Action, ...], simulator: MockCity | None) -> list[PlanStep]:
        city = simulator.clone() if simulator else MockCity()
        city.set_state(state)
        steps = []
        for index, action in enumerate(actions):
            expected = city.step([action])
            steps.append(PlanStep(index, action, expected, action.expected_effect, action.max_retries))
        return steps


class SafeStarterPlanner:
    """Compatibility facade over the deterministic multi-step manager."""

    def __init__(self, manager: StrategicManager | None = None, max_depth: int = 3):
        self.manager = manager or StrategicManager()
        self.multi = MultiStepPlanner(self.manager, max_depth=max_depth)

    def plan(self, observation: Observation, state: CityState | None = None) -> Plan:
        if state is None:
            return Plan([], "Observation-only mode; normalized city state is not available.")
        return self.multi.search(state)
