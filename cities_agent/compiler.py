from __future__ import annotations

from dataclasses import dataclass

from .action_mapping import BuildSpec, CitiesSkylinesActionMapper
from .actions import Action, SafetyClass
from .calibration import Calibration
from .intent import Intent, IntentKind


@dataclass(frozen=True)
class CompileResult:
    actions: tuple[Action, ...]
    reason: str = ""


class IntentCompiler:
    """Compile validated semantic intents into calibrated low-level actions.

    The compiler has no OS-input capability. It only produces typed actions;
    the safety policy, pilot guard, controller and verifier remain downstream.
    """

    def __init__(self, calibration: Calibration):
        self.mapper = CitiesSkylinesActionMapper(calibration)

    def compile(self, intent: Intent) -> CompileResult:
        if intent.confidence < 0.80:
            return CompileResult((), "Intent confidence is below the execution threshold.")
        try:
            if intent.kind == IntentKind.OBSERVE:
                return CompileResult((Action(type=__import__('cities_agent.actions', fromlist=['ActionType']).ActionType.OBSERVE),), "Observation intent.")
            if intent.kind == IntentKind.ZONE:
                if intent.point is None:
                    raise ValueError("zone intent requires point")
                return CompileResult(self.mapper.zone(intent.target, intent.point), "Compiled zoning intent.")
            if intent.kind == IntentKind.CONSTRUCT:
                if intent.point is None or intent.end is None:
                    raise ValueError("construction intent requires point and end")
                return CompileResult(self.mapper.build_road(BuildSpec(intent.point, intent.end, intent.target or "road")), "Compiled construction intent.")
            if intent.kind == IntentKind.UTILITY:
                return CompileResult(self.mapper.utility(intent.target), "Compiled utility intent.")
            if intent.kind == IntentKind.SERVICE:
                return CompileResult(self.mapper.service(intent.target), "Compiled service intent.")
            if intent.kind == IntentKind.BULLDOZE:
                if intent.point is None:
                    raise ValueError("bulldoze intent requires point")
                return CompileResult(self.mapper.bulldoze(intent.point), "Compiled bulldoze intent.")
            if intent.kind == IntentKind.BUDGET:
                if intent.value is None:
                    raise ValueError("budget intent requires value")
                return CompileResult(self.mapper.budget(intent.target, int(intent.value)), "Compiled budget intent.")
            if intent.kind == IntentKind.CAMERA:
                if intent.point is None:
                    raise ValueError("camera intent requires point")
                return CompileResult((Action(__import__('cities_agent.actions', fromlist=['ActionType']).ActionType.CAMERA, self.mapper._pixel(intent.point), SafetyClass.REVERSIBLE, expected_effect="Move camera to calibrated point."),), "Compiled camera intent.")
            raise ValueError(f"Unsupported intent kind: {intent.kind.value}")
        except (ValueError, KeyError) as exc:
            return CompileResult((), str(exc))
