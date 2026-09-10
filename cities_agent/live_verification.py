from __future__ import annotations

from .actions import Action
from .semantic_verification import SemanticVerificationEngine, default_semantic_rules
from .state import CityState
from .verification import ActionVerifier, VerificationResult
from .perception import Observation


class LiveSemanticVerifier:
    """Composite verifier: deterministic state rules first, image verifier second.

    Generic image change remains subject to the caller's confidence threshold and
    therefore cannot silently turn into execution authority.
    """

    def __init__(self, semantic: SemanticVerificationEngine | None = None, fallback: ActionVerifier | None = None):
        self.semantic = semantic or SemanticVerificationEngine(default_semantic_rules())
        self.fallback = fallback or ActionVerifier()

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
