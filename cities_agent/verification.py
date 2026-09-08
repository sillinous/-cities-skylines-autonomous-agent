from __future__ import annotations

from dataclasses import dataclass

from .actions import Action, ActionType
from .perception import Observation
from .state import CityState


@dataclass
class VerificationResult:
    success: bool
    reason: str
    confidence: float = 0.0


class ActionVerifier:
    """Verify game effects using typed state deltas before weak visual evidence."""

    def verify(
        self,
        before: Observation,
        after: Observation,
        action_name: str,
        *,
        before_state: CityState | None = None,
        after_state: CityState | None = None,
        action: Action | None = None,
    ) -> VerificationResult:
        if (before.width, before.height) != (after.width, after.height):
            return VerificationResult(False, "Screen dimensions changed.")
        if action_name == "noop":
            return VerificationResult(True, "No-op verified.", 1.0)
        if before_state is not None and after_state is not None:
            result = self._verify_state_delta(before_state, after_state, action)
            if result is not None:
                return result
        if self._image_changed(before, after):
            return VerificationResult(True, "Screen changed, but no semantic state delta was available.", 0.55)
        return VerificationResult(False, "No observable state or screen change detected.", 0.20)

    @staticmethod
    def _verify_state_delta(before: CityState, after: CityState, action: Action | None):
        if action is None:
            return None
        if action.type == ActionType.ZONE and action.args:
            zone = str(action.args[0]).lower()
            field = f"{zone}_demand"
            b, a = getattr(before, field, None), getattr(after, field, None)
            if b is not None and a is not None and a < b:
                return VerificationResult(True, f"{zone} demand decreased as expected.", 0.90)
        if action.type == ActionType.BUILD_ROAD:
            b, a = before.traffic_percent, after.traffic_percent
            if b is not None and a is not None and a > b:
                return VerificationResult(True, "Traffic metric improved after road action.", 0.85)
        if action.type == ActionType.UTILITY and action.args:
            utility = str(action.args[0]).lower()
            field = {"power": "power_ok", "water": "water_ok", "sewage": "sewage_ok"}.get(utility)
            if field and getattr(after, field) is True and getattr(before, field) is not True:
                return VerificationResult(True, f"{utility} status recovered.", 0.90)
        if action.type == ActionType.SERVICE and action.args:
            service = str(action.args[0]).lower()
            b = before.service_coverage.get(service)
            a = after.service_coverage.get(service)
            if b is not None and a is not None and a > b:
                return VerificationResult(True, f"{service} coverage increased.", 0.90)
        if action.type == ActionType.BUDGET and len(action.args) == 2:
            category, value = str(action.args[0]).lower(), int(action.args[1])
            if after.budgets.get(category) == value and before.budgets.get(category) != value:
                return VerificationResult(True, f"{category} budget changed to {value}%.", 0.95)
        if action.type == ActionType.BULLDOZE and before.money is not None and after.money is not None:
            if after.money > before.money:
                return VerificationResult(True, "Bulldoze produced the modeled refund.", 0.85)
        return None

    @staticmethod
    def _image_changed(before: Observation, after: Observation, threshold: float = 0.01) -> bool:
        a = before.screenshot.resize((64, 36)).convert("L")
        b = after.screenshot.resize((64, 36)).convert("L")
        pixels_a, pixels_b = list(a.getdata()), list(b.getdata())
        changed = sum(abs(x - y) > 8 for x, y in zip(pixels_a, pixels_b))
        return changed / len(pixels_a) >= threshold
