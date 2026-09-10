from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .actions import Action, ActionType
from .state import CityState
from .verification import VerificationResult


@dataclass(frozen=True)
class VerificationContract:
    """Action-specific deterministic evidence contract.

    A contract must identify the intended semantic effect; unrelated state
    changes are deliberately insufficient evidence.
    """

    name: str
    check: Callable[[CityState, CityState, Action], bool]
    confidence: float = 0.95

    def verify(self, before: CityState, after: CityState, action: Action) -> VerificationResult:
        try:
            if self.check(before, after, action):
                return VerificationResult(True, f"Verification contract '{self.name}' satisfied.", self.confidence)
        except (KeyError, TypeError, ValueError, IndexError):
            pass
        return VerificationResult(False, f"Verification contract '{self.name}' not satisfied.", 0.0)


def _target_from_effect(action: Action, prefix: str) -> str | None:
    effect = action.expected_effect.strip()
    if not effect.startswith(prefix):
        return None
    value = effect[len(prefix):].strip()
    return value or None


def default_contracts() -> dict[ActionType, VerificationContract]:
    """Return conservative contracts for state-bearing final actions."""

    def zone(before: CityState, after: CityState, action: Action) -> bool:
        target = _target_from_effect(action, "Zone ")
        if not target:
            return False
        field = {"residential": "residential_demand", "commercial": "commercial_demand", "industrial": "industrial_demand"}.get(target.lower())
        if not field:
            return False
        old, new = getattr(before, field), getattr(after, field)
        return old is not None and new is not None and new != old

    def road(before: CityState, after: CityState, action: Action) -> bool:
        return before.traffic_percent is not None and after.traffic_percent is not None and after.traffic_percent != before.traffic_percent

    def utility(before: CityState, after: CityState, action: Action) -> bool:
        target = _target_from_effect(action, "Place utility:")
        if not target:
            return False
        old = getattr(before, f"{target}_ok", None)
        new = getattr(after, f"{target}_ok", None)
        return old is False and new is True

    def service(before: CityState, after: CityState, action: Action) -> bool:
        target = _target_from_effect(action, "Place service:")
        if not target:
            return False
        old = before.service_coverage.get(target)
        new = after.service_coverage.get(target)
        return old is not None and new is not None and new > old

    def budget(before: CityState, after: CityState, action: Action) -> bool:
        target = _target_from_effect(action, "Set budget ")
        if not target or " to " not in target:
            return False
        category, raw = target.rsplit(" to ", 1)
        if not raw.endswith("%"):
            return False
        try:
            expected = int(raw[:-1])
        except ValueError:
            return False
        actual = after.budgets.get(category.lower())
        return actual == expected and before.budgets.get(category.lower()) != expected

    return {
        ActionType.ZONE: VerificationContract("zone_demand_delta", zone),
        ActionType.DRAG: VerificationContract("road_traffic_delta", road),
        ActionType.UTILITY: VerificationContract("utility_recovery", utility),
        ActionType.SERVICE: VerificationContract("service_coverage_delta", service),
        ActionType.BUDGET: VerificationContract("budget_exact_value", budget),
    }


class ActionSpecificVerifier:
    """Verify only with evidence tied to the action's declared semantics."""

    def __init__(self, contracts: dict[ActionType, VerificationContract] | None = None):
        self.contracts = contracts or default_contracts()

    def verify(self, before: CityState, after: CityState, action: Action) -> VerificationResult:
        contract = self.contracts.get(action.type)
        if contract is None:
            return VerificationResult(False, f"No action-specific contract for '{action.type.value}'.", 0.0)
        return contract.verify(before, after, action)
