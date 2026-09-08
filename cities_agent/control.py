from __future__ import annotations

import pyautogui

from .actions import Action, ActionResult, ActionType
from .policy import SafetyPolicy


class SafetyController:
    """Execute only policy-authorized low-level input and report dispatch status."""

    def __init__(self, policy: SafetyPolicy | None = None, *, allow_input: bool | None = None):
        if policy is None:
            policy = SafetyPolicy(allow_input=bool(allow_input)) if allow_input is not None else SafetyPolicy()
        self.policy = policy
        self.stopped = False

    def emergency_stop(self):
        self.stopped = True
        for key in ("ctrl", "shift", "alt"):
            pyautogui.keyUp(key)

    def execute(self, action: Action) -> ActionResult:
        if self.stopped:
            return ActionResult(action, False, False, "Emergency stop is active.")
        authorized, reason = self.policy.authorize(action)
        if not authorized:
            return ActionResult(action, False, False, reason)
        try:
            if action.type == ActionType.OBSERVE:
                return ActionResult(action, True, False, "Observation requested; no input dispatched.", 1)
            if action.type == ActionType.KEY:
                pyautogui.press(*action.args)
            elif action.type == ActionType.CAMERA:
                if len(action.args) != 2:
                    raise ValueError("camera requires x, y")
                pyautogui.moveTo(*action.args, duration=0.15)
            elif action.type == ActionType.CLICK:
                pyautogui.click(*action.args)
            elif action.type == ActionType.SELECT_TOOL:
                if len(action.args) != 2:
                    raise ValueError("select_tool requires calibrated x, y")
                pyautogui.click(*action.args)
            elif action.type == ActionType.DRAG:
                if len(action.args) != 4:
                    raise ValueError("drag requires x1, y1, x2, y2")
                pyautogui.moveTo(action.args[0], action.args[1], duration=0.1)
                pyautogui.dragTo(action.args[2], action.args[3], duration=0.25)
            else:
                return ActionResult(action, False, False, f"No low-level mapping for {action.type.value}.")
            return ActionResult(action, True, False, "Input dispatched; awaiting game verification.", 1)
        except Exception as exc:
            return ActionResult(action, False, False, f"Input dispatch failed: {exc}", 1)
