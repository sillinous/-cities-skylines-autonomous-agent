from dataclasses import dataclass
from .actions import Action, SafetyClass


@dataclass(frozen=True)
class SafetyPolicy:
    allow_input: bool = False
    allow_reversible: bool = False
    allow_destructive: bool = False
    max_actions_per_cycle: int = 1

    def authorize(self, action: Action) -> tuple[bool, str]:
        if self.max_actions_per_cycle < 0:
            return False, "Invalid action limit."
        if not self.allow_input and action.safety != SafetyClass.READ_ONLY:
            return False, "Input is disabled by safety policy."
        if action.safety == SafetyClass.REVERSIBLE and not self.allow_reversible:
            return False, "Reversible input is disabled by safety policy."
        if action.safety == SafetyClass.DESTRUCTIVE and not self.allow_destructive:
            return False, "Destructive input is disabled by safety policy."
        return True, "Authorized."
