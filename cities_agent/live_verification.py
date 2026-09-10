from __future__ import annotations

from .actions import Action
from .semantic_verification import SemanticVerificationEngine, default_semantic_rules
from .state import CityState
from .verification import ActionVerifier, VerificationResult
from .verification_contracts import ActionSpecificVerifier
from .perception import Observation


class LiveSemanticVerifier:
    """Composite verifier with strict action-specific evidence precedence.

    Compiler-tagged semantic effects must satisfy their deterministic contract;
    they never fall through to unrelated state deltas or generic screen-change
    evidence. Intermediate UI actions also cannot be accepted merely because the
    screen changed.
    """

    def __init__(self, semantic: SemanticVerificationEngine | None = None, fallback: ActionVerifier | None = None, specific: ActionSpecificVerifier | None = None):
        self.semantic = semantic or SemanticVerificationEngine(default_semantic_rules())
        self.fallback = fallback or ActionVerifier()
        self.specific = specific or ActionSpecificVerifier()

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
        if before_state is not None and after_state is not None and action is not None:
            phase = action.meta("phase")
            semantic_kind = action.meta("semantic_kind")
            if semantic_kind:
                if phase != "effect":
                    return VerificationResult(False, "Intermediate semantic action requires dedicated UI evidence; generic screen change is insufficient.", 0.0)
                if self.specific.has_contract(action):
                    return self.specific.verify(before_state, after_state, action)
                return VerificationResult(False, "Semantic effect has no deterministic verification contract.", 0.0)
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
