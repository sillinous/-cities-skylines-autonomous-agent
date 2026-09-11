from __future__ import annotations

from dataclasses import dataclass

from .budget_control import BudgetControlProfile
from .calibration_profile import CalibrationProfile
from .compiler import IntentCompiler
from .ocr import OcrEngine
from .perception import Observation
from .state_parser import StateParser, StateParserProfile
from .ui_evidence import OcrUiEvidenceVerifier, UiEvidenceRule


@dataclass(frozen=True)
class LiveGameProfile:
    """Single named profile tying resolution, OCR state, UI evidence, and input calibration together."""

    calibration: CalibrationProfile
    state: StateParserProfile
    ui_rules: tuple[UiEvidenceRule, ...] = ()
    budget: BudgetControlProfile | None = None

    def validate_observation(self, observation: Observation) -> None:
        self.calibration.validate_observation(observation)
        self.state.validate(observation)

    @property
    def name(self) -> str:
        return self.calibration.name

    def state_reader(self, ocr: OcrEngine | None = None) -> StateParser:
        return StateParser(ocr or OcrEngine(), profile=self.state)

    def compiler(self) -> IntentCompiler:
        return IntentCompiler(self.calibration.calibration, budget_profile=self.budget)

    def ui_verifier(self, ocr: OcrEngine | None = None) -> OcrUiEvidenceVerifier:
        return OcrUiEvidenceVerifier(self.ui_rules, ocr=ocr)

    def ui_evidence_configured(self) -> bool:
        return bool(self.ui_rules)


def profile_from_calibration(
    calibration: CalibrationProfile,
    state: StateParserProfile,
    *,
    ui_rules: tuple[UiEvidenceRule, ...] = (),
    budget: BudgetControlProfile | None = None,
) -> LiveGameProfile:
    if (calibration.calibration.width, calibration.calibration.height) != (state.width, state.height):
        raise ValueError("Calibration and state parser profiles must use the same resolution.")
    return LiveGameProfile(calibration, state, tuple(ui_rules), budget)
