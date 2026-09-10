from __future__ import annotations

from dataclasses import dataclass, replace

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


def _tag(actions: tuple[Action, ...], **metadata: str) -> tuple[Action, ...]:
    """Attach immutable compiler facts without changing low-level action types."""
    tags = tuple((str(k), str(v)) for k, v in metadata.items())
    return tuple(replace(action, metadata=action.metadata + tags) for action in actions)


def _effect_last(actions: tuple[Action, ...]) -> tuple[Action, ...]:
    if not actions:
        return actions
    return actions[:-1] + (replace(actions[-1], metadata=actions[-1].metadata[:-1] + (("phase", "effect"),)),)


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
                actions = _effect_last(_tag(self.mapper.zone(intent.target, intent.point), semantic_kind="zone", target=intent.target, phase="tool"))
                return CompileResult(actions, "Compiled zoning intent.")
            if intent.kind == IntentKind.CONSTRUCT:
                actions = _effect_last(_tag(self.mapper.build_road(BuildSpec(intent.point, intent.end, intent.target or "road")), semantic_kind="construct", target=intent.target or "road", phase="tool"))
                return CompileResult(actions, "Compiled construction intent.")
            if intent.kind == IntentKind.UTILITY:
                actions = _effect_last(_tag(self.mapper.utility(intent.target, intent.point), semantic_kind="utility", target=intent.target, phase="tool"))
                return CompileResult(actions, "Compiled utility placement intent.")
            if intent.kind == IntentKind.SERVICE:
                actions = _effect_last(_tag(self.mapper.service(intent.target, intent.point), semantic_kind="service", target=intent.target, phase="tool"))
                return CompileResult(actions, "Compiled service placement intent.")
            if intent.kind == IntentKind.BULLDOZE:
                actions = _effect_last(_tag(self.mapper.bulldoze(intent.point), semantic_kind="bulldoze", phase="tool"))
                return CompileResult(actions, "Compiled bulldoze intent.")
            if intent.kind == IntentKind.BUDGET:
                actions = self.budget_controller.compile(intent.target, int(intent.value))
                phases = ("panel", "category", "effect")
                tagged = tuple(
                    replace(action, metadata=action.metadata + (("semantic_kind", "budget"), ("target", intent.target), ("value", str(int(intent.value))), ("phase", phase)))
                    for action, phase in zip(actions, phases)
                )
                return CompileResult(tagged, "Compiled calibrated budget intent.")
            if intent.kind == IntentKind.CAMERA:
                action = Action(ActionType.CAMERA, self.mapper._pixel(intent.point), SafetyClass.REVERSIBLE, expected_effect="Move camera to calibrated point.")
                return CompileResult(_tag((action,), semantic_kind="camera", phase="effect"), "Compiled camera intent.")
            raise ValueError(f"Unsupported intent kind: {intent.kind.value}")
        except (ValueError, KeyError) as exc:
            return CompileResult((), str(exc))
