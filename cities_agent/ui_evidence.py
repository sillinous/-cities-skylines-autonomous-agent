from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .actions import Action
from .ocr import OcrEngine
from .perception import Observation
from .verification import VerificationResult


@dataclass(frozen=True)
class UiEvidenceRule:
    """OCR-backed evidence contract for an intermediate UI state.

    The region and expected tokens are calibration/profile data. No default rule
    is supplied because exact UI text/layout varies by game version, DLC, UI
    scale, language, and user configuration.
    """

    name: str
    semantic_kind: str
    phase: str
    region: tuple[float, float, float, float]
    tokens: tuple[str, ...]
    confidence: float = 0.90
    require_all_tokens: bool = True

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("UI evidence rule name must not be empty.")
        if not self.semantic_kind.strip() or not self.phase.strip():
            raise ValueError("UI evidence semantic_kind and phase are required.")
        if self.phase == "effect":
            raise ValueError("UI evidence rules are for intermediate states, not final effects.")
        x1, y1, x2, y2 = self.region
        if not (0.0 <= x1 < x2 <= 1.0 and 0.0 <= y1 < y2 <= 1.0):
            raise ValueError("UI evidence region must be normalized and have positive area.")
        if not self.tokens or any(not token.strip() for token in self.tokens):
            raise ValueError("UI evidence requires at least one non-empty token.")
        if not 0.0 < self.confidence <= 1.0:
            raise ValueError("UI evidence confidence must be in (0, 1].")

    def matches(self, action: Action) -> bool:
        return (
            action.meta("semantic_kind") == self.semantic_kind
            and action.meta("phase") == self.phase
        )


class OcrUiEvidenceVerifier:
    """Verify intermediate tool/panel states using explicitly profiled OCR text."""

    def __init__(self, rules: Iterable[UiEvidenceRule] = (), ocr: OcrEngine | None = None):
        self.rules = tuple(rules)
        self.ocr = ocr or OcrEngine()
        for rule in self.rules:
            rule.validate()

    @staticmethod
    def _crop(observation: Observation, region: tuple[float, float, float, float]):
        x1, y1, x2, y2 = region
        box = (
            round(x1 * observation.width),
            round(y1 * observation.height),
            round(x2 * observation.width),
            round(y2 * observation.height),
        )
        return observation.screenshot.crop(box)

    def verify(self, before: Observation, after: Observation, action: Action) -> VerificationResult:
        matching = [rule for rule in self.rules if rule.matches(action)]
        if not matching:
            return VerificationResult(False, "No profiled OCR UI-evidence contract matches the intermediate action.", 0.0)

        for rule in matching:
            text = self.ocr.text(self._crop(after, rule.region)).lower()
            tokens = tuple(token.strip().lower() for token in rule.tokens)
            present = [token for token in tokens if token in text]
            satisfied = len(present) == len(tokens) if rule.require_all_tokens else bool(present)
            if satisfied:
                return VerificationResult(
                    True,
                    f"OCR UI-evidence rule '{rule.name}' verified: {', '.join(present)}.",
                    rule.confidence,
                )

        return VerificationResult(False, "Profiled OCR UI-evidence rules did not match the observed intermediate state.", 0.0)
