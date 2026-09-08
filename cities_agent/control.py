import pyautogui
from .actions import Action, ActionType
from .policy import SafetyPolicy


class SafetyController:
    def __init__(self, policy: SafetyPolicy | None = None):
        self.policy = policy or SafetyPolicy()
        self.stopped = False

    def emergency_stop(self):
        self.stopped = True
        for key in ("ctrl", "shift", "alt"):
            pyautogui.keyUp(key)

    def execute(self, action: Action) -> bool:
        if self.stopped:
            return False
        authorized, _ = self.policy.authorize(action)
        if not authorized:
            return False
        if action.type == ActionType.OBSERVE:
            return True
        if action.type == ActionType.KEY:
            pyautogui.press(*action.args)
            return True
        if action.type == ActionType.CAMERA:
            pyautogui.moveTo(*action.args, duration=0.15)
            return True
        if action.type == ActionType.CLICK:
            pyautogui.click(*action.args)
            return True
        if action.type == ActionType.DRAG:
            if len(action.args) != 4:
                raise ValueError("drag requires x1, y1, x2, y2")
            pyautogui.moveTo(action.args[0], action.args[1], duration=0.1)
            pyautogui.dragTo(action.args[2], action.args[3], duration=0.25)
            return True
        raise ValueError(f"Unsupported action: {action.type.value}")
