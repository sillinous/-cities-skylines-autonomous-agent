from __future__ import annotations

from dataclasses import dataclass

from .actions import Action, ActionType, SafetyClass
from .calibration import Calibration


@dataclass(frozen=True)
class CameraPoint:
    x: float
    y: float

    def validate(self) -> None:
        if not (0.0 <= self.x <= 1.0 and 0.0 <= self.y <= 1.0):
            raise ValueError("Camera coordinates must be normalized to [0, 1].")


class CameraNavigator:
    """Translate semantic camera requests into calibrated low-level actions."""

    def __init__(self, calibration: Calibration):
        self.calibration = calibration

    def move_to(self, point: CameraPoint) -> Action:
        point.validate()
        x, y = self.calibration.pixel("viewport_center")
        tx = round(point.x * self.calibration.width)
        ty = round(point.y * self.calibration.height)
        return Action(
            ActionType.CAMERA,
            (tx, ty),
            SafetyClass.REVERSIBLE,
            expected_effect=f"Move camera interaction focus toward ({point.x:.3f}, {point.y:.3f}).",
        )

    def pan(self, start: CameraPoint, end: CameraPoint) -> Action:
        start.validate()
        end.validate()
        return Action(
            ActionType.DRAG,
            (
                round(start.x * self.calibration.width),
                round(start.y * self.calibration.height),
                round(end.x * self.calibration.width),
                round(end.y * self.calibration.height),
            ),
            SafetyClass.REVERSIBLE,
            expected_effect="Pan the camera viewport.",
        )

    def zoom(self, direction: str, steps: int = 1) -> Action:
        direction = direction.lower()
        if direction not in {"in", "out"}:
            raise ValueError("direction must be 'in' or 'out'")
        if steps < 1:
            raise ValueError("steps must be positive")
        key = "pageup" if direction == "in" else "pagedown"
        return Action(
            ActionType.KEY,
            (key, steps),
            SafetyClass.REVERSIBLE,
            expected_effect=f"Zoom {direction} by {steps} step(s).",
        )

    def rotate(self, direction: str, steps: int = 1) -> Action:
        direction = direction.lower()
        if direction not in {"left", "right"}:
            raise ValueError("direction must be 'left' or 'right'")
        if steps < 1:
            raise ValueError("steps must be positive")
        key = "q" if direction == "left" else "e"
        return Action(
            ActionType.KEY,
            (key, steps),
            SafetyClass.REVERSIBLE,
            expected_effect=f"Rotate camera {direction} by {steps} step(s).",
        )

    def pause_toggle(self) -> Action:
        return Action(ActionType.KEY, ("space",), SafetyClass.REVERSIBLE, expected_effect="Toggle simulation pause state.")

    def set_speed(self, speed: int) -> Action:
        if speed not in {1, 2, 3}:
            raise ValueError("simulation speed must be 1, 2, or 3")
        return Action(ActionType.KEY, (str(speed),), SafetyClass.REVERSIBLE, expected_effect=f"Set simulation speed to {speed}.")
