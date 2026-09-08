from __future__ import annotations

from dataclasses import dataclass

from .action_mapping import BuildSpec, CitiesSkylinesActionMapper
from .actions import Action, ActionType, SafetyClass
from .budget_control import BudgetControlProfile, CalibratedBudgetController
from .calibration import Calibration
from .intent import Intent, IntentKind
from .intent_validation import validate_intent


@dataclass(frozen=True)
class CompileResult:
    actions: tuple[Action, ...]
    reason: str = ""


class IntentCompiler:
    """Compile semantic intents into calibrated typed actions without dispatching."""

    def __init__(self, calibration: Calibration, *, budget_profile: BudgetControlProfile | None = None):
        self.mapper = CitiesSkylinesActionMapper(calibration)
        self.budget_controller = CalibratedBudgetController(calibration, budget_profile)

    def compile(self, intent: Intent) -> CompileResult:
        try:
            validate_intent(intent)
            if intent.kind == IntentKind.OBSERVE:
                return CompileResult((Action(ActionType.OBSERVE),), "Observation intent.")
            if intent.kind == IntentKind.ZONE:
                return CompileResult(self.mapper.zone(intent.target, intent.point), "Compiled zoning intent.")
            if intent.kind == IntentKind.CONSTRUCT:
                return CompileResult(self.mapper.build_road(BuildSpec(intent.point, intent.end, intent.target or "road")), "Compiled construction intent.")
            if intent.kind == IntentKind.UTILITY:
                return CompileResult(self.mapper.utility(intent.target, intent.point), "Compiled utility placement intent.")
            if intent.kind == IntentKind.SERVICE:
                return CompileResult(self.mapper.service(intent.target, intent.point), "Compiled service placement intent.")
            if intent.kind == IntentKind.BULLDOZE:
                return CompileResult(self.mapper.bulldoze(intent.point), "Compiled bulldoze intent.")
            if intent.kind == IntentKind.BUDGET:
                return CompileResult(self.budget_controller.compile(intent.target, int(intent.value)), "Compiled calibrated budget intent.")
            if intent.kind == IntentKind.CAMERA:
                return CompileResult((Action(ActionType.CAMERA, self.mapper._pixel(intent.point), SafetyClass.REVERSIBLE, expected_effect="Move camera to calibrated point."),), "Compiled camera intent.")
            raise ValueError(f"Unsupported intent kind: {intent.kind.value}")
        except (ValueError, KeyError) as exc:
            return CompileResult((), str(exc))
