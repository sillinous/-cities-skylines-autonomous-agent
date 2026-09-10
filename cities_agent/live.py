from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .actions import Action, ActionResult, SafetyClass
from .audit import AuditLog
from .calibration import Calibration
from .checkpoint import Checkpoint, CheckpointStore
from .compiler import IntentCompiler
from .intent import Intent
from .perception import Observation, ScreenObserver
from .pilot import PilotGuard
from .state import CityState
from .telemetry import TelemetryLog, record_action
from .verification import ActionVerifier, VerificationResult


@dataclass(frozen=True)
class LiveCycleResult:
    observation: Observation
    state: CityState
    intent: Intent | None
    actions: tuple[Action, ...]
    results: tuple[ActionResult, ...]
    verification: tuple[VerificationResult, ...]
    halted: bool


class LivePilot:
    """Bounded live-game loop with explicit observation and verification gates.

    The pilot intentionally defaults to dry-run through PilotGuard. Planning or
    perception code can propose semantic intents, but no OS input is dispatched
    unless pilot preflight, safety policy, calibration, and foreground checks
    all pass.

    Multi-action semantic intents are retained as a checkpointed pending queue.
    This prevents a per-cycle action budget from silently discarding the rest of
    a compiled transaction. Each dispatched sub-action still passes the pilot
    gate and semantic verification before the next sub-action is attempted.
    """

    def __init__(
        self,
        *,
        observer: ScreenObserver,
        state_reader: Callable[[Observation], CityState],
        intent_provider: Callable[[Observation, CityState], Intent | None],
        controller,
        pilot: PilotGuard,
        compiler: IntentCompiler | None = None,
        verifier: ActionVerifier | None = None,
        telemetry: TelemetryLog | None = None,
        audit: AuditLog | None = None,
        checkpoints: CheckpointStore | None = None,
        episode_id: str = "live",
    ):
        self.observer = observer
        self.state_reader = state_reader
        self.intent_provider = intent_provider
        self.controller = controller
        self.pilot = pilot
        self.compiler = compiler
        self.verifier = verifier or ActionVerifier()
        self.telemetry = telemetry or TelemetryLog()
        self.audit = audit or AuditLog()
        self.checkpoints = checkpoints
        self.episode_id = episode_id
        self.step = 0
        self.halted = False
        self.pending_actions: tuple[Action, ...] = ()

    def set_calibration(self, calibration: Calibration, observation: Observation) -> None:
        self.pilot.set_calibration(calibration, observation)
        self.compiler = IntentCompiler(calibration)
        self.telemetry.record("calibration", "Calibration established", width=calibration.width, height=calibration.height)

    def halt(self, reason: str = "Live pilot halted.") -> None:
        self.halted = True
        self.pending_actions = ()
        self.pilot.halt()
        self.controller.emergency_stop()
        self.audit.record("pilot_halt", reason)
        self.telemetry.record("pilot_halt", reason)

    def run_once(self, *, max_actions: int = 1) -> LiveCycleResult:
        if self.halted:
            observation = self.observer.capture()
            state = self.state_reader(observation)
            return LiveCycleResult(observation, state, None, (), (), (), True)
        if max_actions < 1:
            raise ValueError("max_actions must be positive")

        self.pilot.reset_cycle()
        before = self.observer.capture()
        state = self.state_reader(before)
        self.telemetry.record("observation", "Live observation captured", width=before.width, height=before.height)

        intent = None
        if not self.pending_actions:
            intent = self.intent_provider(before, state)
            if intent is None:
                self.telemetry.record("decision", "No intent proposed")
                self._checkpoint(state, ())
                self.step += 1
                return LiveCycleResult(before, state, None, (), (), (), False)

            self.telemetry.record("intent", intent.kind.value, target=intent.target, confidence=intent.confidence)
            if self.compiler is None:
                self.audit.record("pilot_stop", "Cannot compile intent without calibration")
                self.halt("Calibration is required before compiling live input.")
                return LiveCycleResult(before, state, intent, (), (), (), True)

            compiled = self.compiler.compile(intent)
            if not compiled.actions:
                self.audit.record("compile_rejected", compiled.reason)
                self.telemetry.record("compile_rejected", compiled.reason)
                self._checkpoint(state, ())
                self.step += 1
                return LiveCycleResult(before, state, intent, (), (), (), False)
            self.pending_actions = tuple(compiled.actions)

        actions_to_run = self.pending_actions[:max_actions]
        self.pending_actions = self.pending_actions[len(actions_to_run):]
        results: list[ActionResult] = []
        verifications: list[VerificationResult] = []
        current_observation = before
        current_state = state

        for action in actions_to_run:
            gate = self.pilot.authorize(action, current_observation, state=current_state, max_actions=max_actions)
            if not gate.ready:
                self.audit.record("pilot_rejected", gate.reason, action=action.name)
                self.telemetry.record("pilot_rejected", gate.reason, action=action.name)
                if action.safety != SafetyClass.READ_ONLY:
                    self.halt(gate.reason)
                results.append(ActionResult(action, False, False, gate.reason))
                self.pending_actions = (action,) + self.pending_actions
                break

            record_action(self.telemetry, action, state=current_state)
            result = self.controller.execute(action)
            results.append(result)
            if not result.executed:
                self.audit.record("dispatch_failed", result.reason, action=action.name)
                self.telemetry.record("dispatch_failed", result.reason, action=action.name)
                self.pending_actions = (action,) + self.pending_actions
                self.halt(result.reason)
                break

            if action.safety != SafetyClass.READ_ONLY:
                self.pilot.record_dispatch()
                after = self.observer.capture()
                after_state = self.state_reader(after)
                verification = self.verifier.verify(
                    current_observation,
                    after,
                    action.name,
                    before_state=current_state,
                    after_state=after_state,
                    action=action,
                )
                verifications.append(verification)
                self.telemetry.record("verification", verification.reason, action=action.name, success=verification.success, confidence=verification.confidence)
                if not verification.success or verification.confidence < 0.80:
                    self.audit.record("verification_failed", verification.reason, action=action.name)
                    self.halt("Live action could not be semantically verified.")
                    break
                current_observation, current_state = after, after_state

        self._checkpoint(current_state, self.pending_actions)
        self.step += 1
        return LiveCycleResult(current_observation, current_state, intent, actions_to_run, tuple(results), tuple(verifications), self.halted)

    def _checkpoint(self, state: CityState, pending: tuple[Action, ...]) -> None:
        if self.checkpoints is None:
            return
        checkpoint = Checkpoint(
            episode_id=self.episode_id,
            step=self.step,
            state=state,
            pending_actions=pending,
            planner_context={"halted": self.halted},
            source="live_pilot",
        )
        self.checkpoints.save(checkpoint)
