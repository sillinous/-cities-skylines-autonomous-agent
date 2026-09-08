from __future__ import annotations

from dataclasses import dataclass

from .actions import Action, ActionResult, ActionType, SafetyClass
from .audit import AuditLog
from .evaluator import Evaluation, SimulationEvaluator
from .goals import Goal, GoalType
from .policy import SafetyPolicy
from .recovery import RecoveryController, RecoveryState
from .simulator import MockCity
from .state import CityState


@dataclass(frozen=True)
class Diagnosis:
    problems: tuple[str, ...]


@dataclass(frozen=True)
class Candidate:
    action: Action
    score: float
    rationale: str
    evaluation: Evaluation | None = None


@dataclass
class ManagerDecision:
    action: Action | None
    rationale: str
    candidates: list[Candidate]
    goals: list[Goal]


class StrategicManager:
    """Deterministic closed-loop manager suitable for simulation first."""

    def __init__(self, policy=None, recovery=None, audit=None, evaluator=None):
        self.policy = policy or SafetyPolicy()
        self.recovery = recovery or RecoveryController()
        self.audit = audit or AuditLog()
        self.evaluator = evaluator or SimulationEvaluator()

    def diagnose(self, state: CityState) -> Diagnosis:
        problems = []
        if state.warnings:
            problems.append("warnings")
        if state.power_ok is False:
            problems.append("power")
        if state.water_ok is False:
            problems.append("water")
        if state.sewage_ok is False:
            problems.append("sewage")
        if state.money is not None and state.money < 0:
            problems.append("budget")
        if state.traffic_percent is not None and state.traffic_percent < 30:
            problems.append("traffic")
        if state.residential_demand is not None and state.residential_demand >= 40:
            problems.append("residential_demand")
        if state.commercial_demand is not None and state.commercial_demand >= 60:
            problems.append("commercial_demand")
        if state.industrial_demand is not None and state.industrial_demand >= 60:
            problems.append("industrial_demand")
        return Diagnosis(tuple(problems))

    def goals_for(self, state: CityState) -> list[Goal]:
        diagnosis = self.diagnose(state)
        goals = []
        if any(p in diagnosis.problems for p in ("power", "water", "sewage", "warnings")):
            goals.append(Goal(GoalType.AVOID_FAILURE, priority=100, hard=True, description="Resolve uncertainty or failures first."))
        if state.money is not None and state.money < 5_000:
            goals.append(Goal(GoalType.MAINTAIN_BUDGET, priority=95, hard=True, description="Preserve a positive cash buffer."))
        if state.traffic_percent is not None and state.traffic_percent < 30:
            goals.append(Goal(GoalType.IMPROVE_TRAFFIC, priority=80, description="Improve traffic without reckless construction."))
        if state.residential_demand is not None and state.residential_demand >= 40:
            goals.append(Goal(GoalType.SATISFY_DEMAND, target="residential", priority=70, description="Satisfy residential demand."))
        if state.commercial_demand is not None and state.commercial_demand >= 60:
            goals.append(Goal(GoalType.SATISFY_DEMAND, target="commercial", priority=60, description="Satisfy commercial demand."))
        if state.industrial_demand is not None and state.industrial_demand >= 60:
            goals.append(Goal(GoalType.SATISFY_DEMAND, target="industrial", priority=60, description="Satisfy industrial demand."))
        return sorted(goals, key=lambda g: g.priority, reverse=True)

    def candidates(self, state: CityState) -> list[Action]:
        actions = []
        if state.residential_demand is not None and state.residential_demand >= 40:
            actions.append(Action(ActionType.ZONE, ("residential",), SafetyClass.REVERSIBLE, expected_effect="Reduce residential demand and increase population."))
        if state.commercial_demand is not None and state.commercial_demand >= 60:
            actions.append(Action(ActionType.ZONE, ("commercial",), SafetyClass.REVERSIBLE, expected_effect="Reduce commercial demand."))
        if state.industrial_demand is not None and state.industrial_demand >= 60:
            actions.append(Action(ActionType.ZONE, ("industrial",), SafetyClass.REVERSIBLE, expected_effect="Reduce industrial demand."))
        if state.traffic_percent is not None and state.traffic_percent < 30 and (state.money or 0) >= 2_000:
            actions.append(Action(ActionType.BUILD_ROAD, (), SafetyClass.REVERSIBLE, expected_effect="Improve modeled traffic."))
        for utility, healthy in (("power", state.power_ok), ("water", state.water_ok), ("sewage", state.sewage_ok)):
            if healthy is False:
                actions.append(Action(ActionType.UTILITY, (utility,), SafetyClass.REVERSIBLE, expected_effect=f"Restore {utility} service."))
        return actions

    def evaluate(self, state: CityState, action: Action, simulator: MockCity | None = None) -> Candidate:
        city = simulator or MockCity()
        evaluation = self.evaluator.evaluate(city, action)
        return Candidate(action, evaluation.score, evaluation.reason, evaluation)

    def plan(self, state: CityState, simulator: MockCity | None = None) -> ManagerDecision:
        goals = self.goals_for(state)
        if goals and goals[0].hard:
            action = Action(ActionType.OBSERVE, safety=SafetyClass.READ_ONLY, expected_effect="Collect more evidence before acting.")
            self.audit.record("plan", "Hard safety goal selected observation-only mode.", action=action.name)
            return ManagerDecision(action, "A hard safety condition is active; observe before changing the city.", [], goals)

        ranked = []
        for action in self.candidates(state):
            authorized, reason = self.policy.authorize(action)
            if not authorized:
                self.audit.record("candidate_blocked", reason, action=action.name)
                continue
            ranked.append(self.evaluate(state, action, simulator))
        ranked.sort(key=lambda c: c.score, reverse=True)
        selected = ranked[0] if ranked and ranked[0].score > 0 else None
        if selected is None:
            rationale = "No safe candidate has positive simulated value."
            self.audit.record("plan", rationale)
            return ManagerDecision(None, rationale, ranked, goals)
        self.audit.record("plan", selected.rationale, action=selected.action.name, score=selected.score)
        return ManagerDecision(selected.action, selected.rationale, ranked, goals)

    def record_execution(self, result: ActionResult) -> None:
        self.audit.record("action", result.reason, action=result.action.name, executed=result.executed, verified=result.verified, attempts=result.attempts)
        if result.verified:
            self.recovery.verified()
            return
        if not result.executed:
            self.recovery.pause()
            self.audit.record("recovery", "Execution did not occur; manager paused.")
            return
        if self.recovery.state == RecoveryState.READY:
            self.recovery.begin()
        if not self.recovery.verification_failed():
            self.audit.record("recovery", "Verification failed and retry budget is exhausted.")
        else:
            self.audit.record("recovery", "Verification failed; retry is permitted.", retries=self.recovery.retries)
