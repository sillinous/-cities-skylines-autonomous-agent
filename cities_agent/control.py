from dataclasses import dataclass
import pyautogui

@dataclass(frozen=True)
class Action:
    name: str
    args: tuple = ()

class SafetyController:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.stopped = False

    def emergency_stop(self):
        self.stopped = True
        for key in ("ctrl", "shift", "alt"):
            pyautogui.keyUp(key)

    def execute(self, action: Action) -> bool:
        if self.stopped or not self.enabled:
            return False
        if action.name == "key":
            pyautogui.press(*action.args)
            return True
        if action.name == "move":
            pyautogui.moveTo(*action.args, duration=0.15)
            return True
        if action.name == "click":
            pyautogui.click(*action.args)
            return True
        raise ValueError(f"Unsupported action: {action.name}")
