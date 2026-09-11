from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .actions import Action, ActionType
from .state import CityState
from .verification import VerificationResult


@dataclass(frozen=True)
class VerificationContract:
    """Action-specific deterministic evidence contract."""

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


def _effect(action: Action, kind: str) -> bool:
    return action.meta("semantic_kind") == kind and action.meta("phase") == "effect"


def default_contracts() -> dict[ActionType, VerificationContract]:
    """Contracts for compiler output; legacy forms are handled separately."""

    def zone(before: CityState, after: CityState, action: Action) -> bool:
        if _effect(action, "zone"):
            target = (action.meta("target") or "").lower()
        elif action.type == ActionType.ZONE and action.args:
            target = str(action.args[0]).lower()
        else:
            return False
        field = {"residential": "residential_demand", "commercial": "commercial_demand", "industrial": "industrial_demand"}.get(target)
        if not field:
            return False
        old, new = getattr(before, field), getattr(after, field)
        return old is not None and new is not None and new != old

    def road(before: CityState, after: CityState, action: Action) -> bool:
        if not (_effect(action, "construct") or action.type in {ActionType.DRAG, ActionType.BUILD_ROAD}):
            return False
        return before.traffic_percent is not None and after.traffic_percent is not None and after.traffic_percent != before.traffic_percent

    def utility(before: CityState, after: CityState, action: Action) -> bool:
        if _effect(action, "utility"):
            target = (action.meta("target") or "").lower()
        elif action.type == ActionType.UTILITY and action.args:
            target = str(action.args[0]).lower()
        else:
            return False
        old = getattr(before, f"{target}_ok", None)
        new = getattr(after, f"{target}_ok", None)
        return old is False and new is True

    def service(before: CityState, after: CityState, action: Action) -> bool:
        if _effect(action, "service"):
            target = (action.meta("target") or "").lower()
        elif action.type == ActionType.SERVICE and action.args:
            target = str(action.args[0]).lower()
        else:
            return False
        old = before.service_coverage.get(target)
        new = after.service_coverage.get(target)
        return old is not None and new is not None and new > old

    def budget(before: CityState, after: CityState, action: Action) -> bool:
        if _effect(action, "budget"):
            category = (action.meta("target") or "").lower()
            try:
                expected = int(action.meta("value") or "")
            except ValueError:
                return False
        elif action.type == ActionType.BUDGET and len(action.args) == 2:
            category, expected = str(action.args[0]).lower(), int(action.args[1])
        else:
            return False
        return after.budgets.get(category) == expected and before.budgets.get(category) != expected

    return {
        ActionType.ZONE: VerificationContract("legacy_zone_demand_delta", zone),
        ActionType.CLICK: VerificationContract("click_semantic_effect", lambda before, after, action: (
            zone(before, after, action) or utility(before, after, action) or service(before, after, action) or budget(before, after, action)
        )),
        ActionType.DRAG: VerificationContract("road_traffic_delta", road),
        ActionType.BUILD_ROAD: VerificationContract("legacy_road_traffic_delta", road),
        ActionType.UTILITY: VerificationContract("legacy_utility_recovery", utility),
        ActionType.SERVICE: VerificationContract("legacy_service_coverage_delta", service),
        ActionType.BUDGET: VerificationContract("legacy_budget_exact_value", budget),
    }


class ActionSpecificVerifier:
    """Verify only with evidence tied to the action's declared semantics."""

    def __init__(self, contracts: dict[ActionType, VerificationContract] | None = None):
        self.contracts = contracts or default_contracts()

    def has_contract(self, action: Action) -> bool:
        if action.meta("semantic_kind"):
            return action.type in self.contracts and action.meta("phase") == "effect" and action.meta("semantic_kind") in {"zone", "construct", "utility", "service", "budget"}
        return action.type in {ActionType.ZONE, ActionType.BUILD_ROAD, ActionType.UTILITY, ActionType.SERVICE, ActionType.BUDGET}

    def verify(self, before: CityState, after: CityState, action: Action) -> VerificationResult:
        contract = self.contracts.get(action.type)
        if contract is None:
            return VerificationResult(False, f"No action-specific contract for '{action.type.value}'.", 0.0)
        if action.meta("semantic_kind") and action.meta("phase") != "effect":
            return VerificationResult(False, f"No action-specific effect contract for '{action.type.value}'.", 0.0)
        return contract.verify(before, after, action)
