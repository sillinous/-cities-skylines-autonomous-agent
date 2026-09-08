from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic, sleep
from typing import Callable

from .actions import Action, ActionResult
from .planner import Plan, PlanStep
from .verification import ActionVerifier, VerificationResult


@dataclass
class ExecutionReport:
    completed: bool
    stopped: bool
    results: list[ActionResult] = field(default_factory=list)
    failed_step: int | None = None
    reason: str = ""


class PlanExecutor:
    """Execute a plan transactionally: dispatch, observe, verify, then continue."""

    def __init__(self, controller, observer, verifier: ActionVerifier | None = None, *, min_verification_confidence: float = 0.80):
        self.controller = controller
        self.observer = observer
        self.verifier = verifier or ActionVerifier()
        self.min_verification_confidence = min_verification_confidence

    def execute(
        self,
        plan: Plan,
        *,
        read_state: Callable | None = None,
        on_divergence: Callable[[int, PlanStep, VerificationResult], None] | None = None,
    ) -> ExecutionReport:
        if not plan.valid:
            return ExecutionReport(False, False, reason="Plan is invalid and cannot be executed.")

        results: list[ActionResult] = []
        for step in plan.steps:
            before = self.observer.capture()
            before_state = read_state(before) if read_state else None
            result = self._dispatch_with_retry(step.action)
            results.append(result)
            if not result.executed:
                self.controller.emergency_stop()
                return ExecutionReport(False, True, results, step.index, result.reason)

            after = self._wait_for_observable_change(before, step.action.timeout_seconds)
            after_state = read_state(after) if read_state else None
            verification = self.verifier.verify(
                before,
                after,
                step.action.name,
                before_state=before_state,
                after_state=after_state,
                action=step.action,
            )
            result.verified = verification.success and verification.confidence >= self.min_verification_confidence
            result.metadata["verification_confidence"] = verification.confidence
            result.metadata["verification_reason"] = verification.reason
            if not result.verified:
                if on_divergence:
                    on_divergence(step.index, step, verification)
                self.controller.emergency_stop()
                return ExecutionReport(False, True, results, step.index, f"Verification failed: {verification.reason}")

        return ExecutionReport(True, False, results, reason="All plan steps executed and verified.")

    def _dispatch_with_retry(self, action: Action) -> ActionResult:
        attempts = 0
        while attempts <= action.max_retries:
            attempts += 1
            result = self.controller.execute(action)
            result.attempts = attempts
            if result.executed:
                return result
            if attempts <= action.max_retries:
                sleep(min(0.25 * attempts, 1.0))
        return result

    def _wait_for_observable_change(self, before, timeout: float):
        deadline = monotonic() + max(0.05, timeout)
        latest = before
        while monotonic() < deadline:
            latest = self.observer.capture()
            if self.verifier._image_changed(before, latest):
                return latest
            sleep(0.05)
        return latest
