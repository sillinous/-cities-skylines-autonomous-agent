from dataclasses import dataclass
from enum import Enum


class RecoveryState(str, Enum):
    READY = "ready"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    RETRYING = "retrying"
    PAUSED = "paused"
    FAILED = "failed"


@dataclass
class RecoveryController:
    max_retries: int = 2
    state: RecoveryState = RecoveryState.READY
    retries: int = 0

    def begin(self):
        self.state = RecoveryState.EXECUTING
        self.retries = 0

    def verification_failed(self) -> bool:
        if self.retries < self.max_retries:
            self.retries += 1
            self.state = RecoveryState.RETRYING
            return True
        self.state = RecoveryState.FAILED
        return False

    def verified(self):
        self.state = RecoveryState.READY
        self.retries = 0

    def pause(self):
        self.state = RecoveryState.PAUSED

    def reset(self):
        self.state = RecoveryState.READY
        self.retries = 0
