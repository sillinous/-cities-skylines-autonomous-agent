from __future__ import annotations

from dataclasses import dataclass

from .actions import Action, ActionType, SafetyClass
from .calibration import Calibration


@dataclass(frozen=True)
class BuildSpec:
    """Game-independent construction intent expressed in normalized coordinates."""

    start: tuple[float, float]
    end: tuple[float, float]
    road_type: str = "road"


class CitiesSkylinesActionMapper:
    """Map semantic intents to calibrated input actions.

    This layer never bypasses the safety policy and does not claim that a
    game action succeeded; verification remains a separate responsibility.
    """

    def __init__(self, calibration: Calibration):
        self.calibration = calibration

    def click_anchor(self, anchor: str, *, safety: SafetyClass = SafetyClass.REVERSIBLE) -> Action:
        x, y = self.calibration.pixel(anchor)
        return Action(ActionType.CLICK, (x, y), safety, expected_effect=f"Click calibrated anchor '{anchor}'.")

    def select_tool(self, anchor: str) -> Action:
        x, y = self.calibration.pixel(anchor)
        return Action(ActionType.SELECT_TOOL, (x, y), SafetyClass.REVERSIBLE, expected_effect=f"Select tool at '{anchor}'.")

    def build_road(self, spec: BuildSpec) -> tuple[Action, ...]:
        self._validate_point(spec.start)
        self._validate_point(spec.end)
        x1, y1 = self._pixel(spec.start)
        x2, y2 = self._pixel(spec.end)
        return (
            Action(ActionType.SELECT_TOOL, (spec.road_type,), SafetyClass.REVERSIBLE, expected_effect=f"Select {spec.road_type} road tool."),
            Action(ActionType.DRAG, (x1, y1, x2, y2), SafetyClass.REVERSIBLE, expected_effect="Draw the requested road segment."),
        )

    def zone(self, zone_type: str, point: tuple[float, float]) -> tuple[Action, ...]:
        self._validate_point(point)
        normalized = zone_type.lower()
        if normalized not in {"residential", "commercial", "industrial"}:
            raise ValueError("zone_type must be residential, commercial, or industrial")
        return (
            Action(ActionType.SELECT_TOOL, (f"zone:{normalized}",), SafetyClass.REVERSIBLE, expected_effect=f"Select {normalized} zoning tool."),
            Action(ActionType.CLICK, self._pixel(point), SafetyClass.REVERSIBLE, expected_effect=f"Zone {normalized} at the requested location."),
        )

    def _pixel(self, point: tuple[float, float]) -> tuple[int, int]:
        return round(point[0] * self.calibration.width), round(point[1] * self.calibration.height)

    @staticmethod
    def _validate_point(point: tuple[float, float]) -> None:
        if len(point) != 2 or any(not 0.0 <= value <= 1.0 for value in point):
            raise ValueError("points must contain two normalized coordinates in [0, 1]")
