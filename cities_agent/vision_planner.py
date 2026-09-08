from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .actions import Action, ActionType, SafetyClass
from .intent import Intent, IntentCandidate, IntentKind
from .policy import SafetyPolicy


@dataclass(frozen=True)
class PlannerDecision:
    candidates: tuple[IntentCandidate, ...]
    selected: IntentCandidate | None
    rationale: str


class VisionIntentPlanner:
    """Convert bounded semantic intents into policy-checked game actions.

    This component deliberately does not call an LLM and never dispatches
    input. Model-generated intents can be supplied later, but deterministic
    validation and the safety policy remain the final gate.
    """

    def __init__(self, policy: SafetyPolicy | None = None, *, min_confidence: float = 0.80):
        self.policy = policy or SafetyPolicy()
        self.min_confidence = min_confidence

    def approve(self, intents: Iterable[Intent]) -> PlannerDecision:
        candidates: list[IntentCandidate] = []
        for intent in intents:
            try:
                intent.validate(self.min_confidence)
                actions = self._actions_for(intent)
                if not actions:
                    candidates.append(IntentCandidate(intent, (), float("-inf"), False, "No deterministic action mapping."))
                    continue
                blocked = []
                for action in actions:
                    allowed, reason = self.policy.authorize(action)
                    if not allowed:
                        blocked.append(reason)
                if blocked:
                    candidates.append(IntentCandidate(intent, actions, float("-inf"), False, "; ".join(blocked)))
                    continue
                score = intent.confidence + (0.1 if intent.kind == IntentKind.OBSERVE else 0.0)
                candidates.append(IntentCandidate(intent, actions, score, True, "Approved by deterministic safety gates."))
            except ValueError as exc:
                candidates.append(IntentCandidate(intent, (), float("-inf"), False, str(exc)))

        approved = [c for c in candidates if c.approved]
        selected = max(approved, key=lambda c: c.score, default=None)
        rationale = selected.reason if selected else "No intent passed deterministic safety gates."
        return PlannerDecision(tuple(candidates), selected, rationale)

    @staticmethod
    def _actions_for(intent: Intent) -> tuple[Action, ...]:
        if intent.kind == IntentKind.OBSERVE:
            return (Action(ActionType.OBSERVE, safety=SafetyClass.READ_ONLY, expected_effect="Collect additional evidence."),)
        if intent.kind == IntentKind.ZONE and intent.target:
            return (Action(ActionType.ZONE, (intent.target.lower(),), SafetyClass.REVERSIBLE, expected_effect=f"Apply {intent.target} zoning."),)
        if intent.kind == IntentKind.UTILITY and intent.target:
            return (Action(ActionType.UTILITY, (intent.target.lower(),), SafetyClass.REVERSIBLE, expected_effect=f"Restore {intent.target} utility."),)
        if intent.kind == IntentKind.SERVICE and intent.target:
            return (Action(ActionType.SERVICE, (intent.target.lower(),), SafetyClass.REVERSIBLE, expected_effect=f"Improve {intent.target} service coverage."),)
        if intent.kind == IntentKind.BULLDOZE and intent.point:
            return (Action(ActionType.BULLDOZE, intent.point, SafetyClass.DESTRUCTIVE, expected_effect="Remove the targeted object."),)
        if intent.kind == IntentKind.BUDGET and intent.target and intent.value is not None:
            return (Action(ActionType.BUDGET, (intent.target, intent.value), SafetyClass.REVERSIBLE, expected_effect=f"Set {intent.target} budget."),)
        return ()
