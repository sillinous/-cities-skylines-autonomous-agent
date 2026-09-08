from dataclasses import dataclass
from .perception import Observation

@dataclass
class VerificationResult:
    success: bool
    reason: str

class ActionVerifier:
    def verify(self, before: Observation, after: Observation, action_name: str):
        if (before.width, before.height) != (after.width, after.height):
            return VerificationResult(False, "Screen dimensions changed.")
        if action_name == "noop":
            return VerificationResult(True, "No-op verified.")
        return VerificationResult(False, "Game-specific verifier not implemented yet.")
