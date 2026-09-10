from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .actions import Action, ActionType
from .state import CityState
from .verification import VerificationResult


@dataclass(frozen=True)
class VerificationContract:
    """Action-specific deterministic evidence contract.

    Contracts consume compiler-supplied semantic metadata rather than parsing
    human-readable expected-effect strings. Missing or mismatched evidence is
    a hard verification failure.
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


def _effect(action: Action, kind: str) -> bool:
    return action.meta("semantic_kind") == kind and action.meta("phase") == "effect"


def default_contracts() -> dict[ActionType, VerificationContract]:
    """Return conservative contracts for state-bearing final actions."""

    def zone(before: CityState, after: CityState, action: Action) -> bool:
        if not _effect(action, "zone"):
            return False
        field = {"residential": "residential_demand", "commercial": "commercial_demand", "industrial": "industrial_demand"}.get((action.meta("target") or "").lower())
        if not field:
            return False
        old, new = getattr(before, field), getattr(after, field)
        return old is not None and new is not None and new != old

    def road(before: CityState, after: CityState, action: Action) -> bool:
        if not _effect(action, "construct"):
            return False
        return before.traffic_percent is not None and after.traffic_percent is not None and after.traffic_percent != before.traffic_percent

    def utility(before: CityState, after: CityState, action: Action) -> bool:
        if not _effect(action, "utility"):
            return False
        target = (action.meta("target") or "").lower()
        old = getattr(before, f"{target}_ok", None)
        new = getattr(after, f"{target}_ok", None)
        return old is False and new is True

    def service(before: CityState, after: CityState, action: Action) -> bool:
        if not _effect(action, "service"):
            return False
        target = (action.meta("target") or "").lower()
        old = before.service_coverage.get(target)
        new = after.service_coverage.get(target)
        return old is not None and new is not None and new > old

    def budget(before: CityState, after: CityState, action: Action) -> bool:
        if not _effect(action, "budget"):
            return False
        category = (action.meta("target") or "").lower()
        try:
            expected = int(action.meta("value") or "")
        except ValueError:
            return False
        actual = after.budgets.get(category)
        return actual == expected and before.budgets.get(category) != expected

    return {
        ActionType.CLICK: VerificationContract("click_semantic_effect", lambda before, after, action: (
            zone(before, after, action) or utility(before, after, action) or service(before, after, action) or budget(before, after, action)
        )),
        ActionType.DRAG: VerificationContract("road_traffic_delta", road),
    }


class ActionSpecificVerifier:
    """Verify only with evidence tied to the action's declared semantics."""

    def __init__(self, contracts: dict[ActionType, VerificationContract] | None = None):
        self.contracts = contracts or default_contracts()

    def has_contract(self, action: Action) -> bool:
        return action.type in self.contracts and action.meta("phase") == "effect" and action.meta("semantic_kind") in {"zone", "construct", "utility", "service", "budget"}

    def verify(self, before: CityState, after: CityState, action: Action) -> VerificationResult:
        contract = self.contracts.get(action.type)
        if contract is None or action.meta("phase") != "effect":
            return VerificationResult(False, f"No action-specific effect contract for '{action.type.value}'.", 0.0)
        return contract.verify(before, after, action)
