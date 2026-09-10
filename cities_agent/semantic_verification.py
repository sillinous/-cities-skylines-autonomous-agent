from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .actions import Action
from .state import CityState
from .verification import VerificationResult


@dataclass(frozen=True)
class SemanticRule:
    """Deterministic verification rule for a semantic action."""

    name: str
    check: Callable[[CityState, CityState, Action], bool]
    confidence: float = 0.95


class SemanticVerificationEngine:
    """Prefer explicit state evidence over generic image change evidence.

    Rules are deterministic and receive the action that was actually dispatched.
    A missing rule never counts as success; callers may fall back to the existing
    ActionVerifier for observation-only or specially instrumented actions.
    """

    def __init__(self, rules: tuple[SemanticRule, ...] = ()):
        self.rules = rules

    def verify(self, before: CityState, after: CityState, action: Action) -> VerificationResult:
        for rule in self.rules:
            try:
                if rule.check(before, after, action):
                    return VerificationResult(True, f"Semantic rule '{rule.name}' verified.", rule.confidence)
            except (KeyError, TypeError, ValueError):
                continue
        return VerificationResult(False, "No deterministic semantic rule verified the action.", 0.0)


def default_semantic_rules() -> tuple[SemanticRule, ...]:
    """Rules for state changes already represented by CityState."""

    def demand_changed(before: CityState, after: CityState, action: Action) -> bool:
        if not action.expected_effect:
            return False
        return any(
            a is not None and b is not None and a != b
            for a, b in (
                (before.residential_demand, after.residential_demand),
                (before.commercial_demand, after.commercial_demand),
                (before.industrial_demand, after.industrial_demand),
            )
        )

    def traffic_changed(before: CityState, after: CityState, action: Action) -> bool:
        return before.traffic_percent is not None and after.traffic_percent is not None and before.traffic_percent != after.traffic_percent

    def utility_recovered(before: CityState, after: CityState, action: Action) -> bool:
        pairs = ((before.power_ok, after.power_ok), (before.water_ok, after.water_ok), (before.sewage_ok, after.sewage_ok))
        return any(old is False and new is True for old, new in pairs)

    def budget_changed(before: CityState, after: CityState, action: Action) -> bool:
        if action.type.value != "click":
            return False
        return bool(before.budgets and after.budgets and before.budgets != after.budgets)

    return (
        SemanticRule("demand_delta", demand_changed),
        SemanticRule("traffic_delta", traffic_changed),
        SemanticRule("utility_recovery", utility_recovered),
        SemanticRule("budget_delta", budget_changed),
    )
