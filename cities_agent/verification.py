from __future__ import annotations

from dataclasses import dataclass

from .actions import Action
from .perception import Observation
from .state import CityState


@dataclass
class VerificationResult:
    success: bool
    reason: str
    confidence: float = 0.0


class ActionVerifier:
    """Verify game effects rather than trusting successful input dispatch."""

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
            return VerificationResult(True, "Screen changed after input; effect requires semantic confirmation.", 0.55)
        return VerificationResult(False, "No observable state or screen change detected.", 0.20)

    @staticmethod
    def _verify_state_delta(before: CityState, after: CityState, action: Action | None):
        if action is None:
            return None
        if action.type.value == "zone" and action.args:
            zone = str(action.args[0]).lower()
            field = f"{zone}_demand"
            if hasattr(before, field) and getattr(before, field) is not None and getattr(after, field) is not None:
                if getattr(after, field) < getattr(before, field):
                    return VerificationResult(True, f"{zone} demand decreased as expected.", 0.90)
        if action.type.value == "build_road" and before.traffic_percent is not None and after.traffic_percent is not None:
            if after.traffic_percent > before.traffic_percent:
                return VerificationResult(True, "Traffic metric improved after road action.", 0.85)
        if action.type.value == "utility" and action.args:
            utility = str(action.args[0]).lower()
            field = {"power": "power_ok", "water": "water_ok", "sewage": "sewage_ok"}.get(utility)
            if field and getattr(after, field) is True and getattr(before, field) is not True:
                return VerificationResult(True, f"{utility} status recovered.", 0.90)
        return None

    @staticmethod
    def _image_changed(before: Observation, after: Observation, threshold: float = 0.01) -> bool:
        # Downsample before comparison to make verification cheap and robust to tiny UI noise.
        a = before.screenshot.resize((64, 36)).convert("L")
        b = after.screenshot.resize((64, 36)).convert("L")
        pixels_a, pixels_b = list(a.getdata()), list(b.getdata())
        changed = sum(abs(x - y) > 8 for x, y in zip(pixels_a, pixels_b))
        return changed / len(pixels_a) >= threshold
