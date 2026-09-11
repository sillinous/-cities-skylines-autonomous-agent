from __future__ import annotations

from .actions import Action
from .semantic_verification import SemanticVerificationEngine, default_semantic_rules
from .state import CityState
from .verification import ActionVerifier, VerificationResult
from .verification_contracts import ActionSpecificVerifier
from .perception import Observation
from .ui_evidence import OcrUiEvidenceVerifier


class LiveSemanticVerifier:
    """Composite verifier with strict evidence precedence.

    Compiler-tagged final effects must satisfy an action-specific state contract.
    Intermediate tool/panel actions require an explicit OCR UI-evidence profile;
    they never fall through to generic screen-change evidence.
    """

    def __init__(
        self,
        semantic: SemanticVerificationEngine | None = None,
        fallback: ActionVerifier | None = None,
        specific: ActionSpecificVerifier | None = None,
        ui_evidence: OcrUiEvidenceVerifier | None = None,
    ):
        self.semantic = semantic or SemanticVerificationEngine(default_semantic_rules())
        self.fallback = fallback or ActionVerifier()
        self.specific = specific or ActionSpecificVerifier()
        self.ui_evidence = ui_evidence or OcrUiEvidenceVerifier()

    def verify(
        self,
        before_observation: Observation,
        after_observation: Observation,
        action_name: str,
        *,
        before_state: CityState | None = None,
        after_state: CityState | None = None,
        action: Action | None = None,
    ) -> VerificationResult:
        if action is not None and action.meta("semantic_kind"):
            phase = action.meta("phase")
            if phase != "effect":
                return self.ui_evidence.verify(before_observation, after_observation, action)
            if before_state is None or after_state is None:
                return VerificationResult(False, "State-bearing semantic effect requires before/after state for verification.", 0.0)
            if self.specific.has_contract(action):
                return self.specific.verify(before_state, after_state, action)
            return VerificationResult(False, "Semantic effect has no deterministic verification contract.", 0.0)

        if before_state is not None and after_state is not None and action is not None:
            semantic = self.semantic.verify(before_state, after_state, action)
            if semantic.success:
                return semantic
        return self.fallback.verify(
            before_observation,
            after_observation,
            action_name,
            before_state=before_state,
            after_state=after_state,
            action=action,
        )
