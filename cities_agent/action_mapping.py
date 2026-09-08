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
    """Map semantic intents to calibrated input actions."""

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
            Action(ActionType.BUILD_ROAD, (spec.road_type, spec.start, spec.end), SafetyClass.REVERSIBLE, expected_effect="Draw the requested road segment."),
            Action(ActionType.DRAG, (x1, y1, x2, y2), SafetyClass.REVERSIBLE, expected_effect="Dispatch the calibrated road drag."),
        )

    def zone(self, zone_type: str, point: tuple[float, float]) -> tuple[Action, ...]:
        self._validate_point(point)
        normalized = zone_type.lower()
        if normalized not in {"residential", "commercial", "industrial"}:
            raise ValueError("zone_type must be residential, commercial, or industrial")
        return (
            Action(ActionType.SELECT_TOOL, (f"zone:{normalized}",), SafetyClass.REVERSIBLE, expected_effect=f"Select {normalized} zoning tool."),
            Action(ActionType.ZONE, (normalized, point), SafetyClass.REVERSIBLE, expected_effect=f"Apply {normalized} zoning."),
            Action(ActionType.CLICK, self._pixel(point), SafetyClass.REVERSIBLE, expected_effect=f"Dispatch zoning click for {normalized}."),
        )

    def utility(self, utility: str) -> Action:
        utility = utility.lower()
        if utility not in {"power", "water", "sewage"}:
            raise ValueError("utility must be power, water, or sewage")
        return Action(ActionType.UTILITY, (utility,), SafetyClass.REVERSIBLE, expected_effect=f"Restore {utility} service.")

    def service(self, service: str) -> Action:
        if not service.strip():
            raise ValueError("service must not be empty")
        return Action(ActionType.SERVICE, (service.lower(),), SafetyClass.REVERSIBLE, expected_effect=f"Improve {service} coverage.")

    def bulldoze(self, point: tuple[float, float]) -> Action:
        self._validate_point(point)
        return Action(ActionType.BULLDOZE, (self._pixel(point),), SafetyClass.DESTRUCTIVE, expected_effect="Remove the targeted construction.")

    def budget(self, category: str, percentage: int) -> Action:
        if not 0 <= percentage <= 150:
            raise ValueError("budget percentage must be between 0 and 150")
        return Action(ActionType.BUDGET, (category.lower(), percentage), SafetyClass.REVERSIBLE, expected_effect=f"Set {category} budget to {percentage}%.")

    def _pixel(self, point: tuple[float, float]) -> tuple[int, int]:
        return round(point[0] * self.calibration.width), round(point[1] * self.calibration.height)

    @staticmethod
    def _validate_point(point: tuple[float, float]) -> None:
        if len(point) != 2 or any(not 0.0 <= value <= 1.0 for value in point):
            raise ValueError("points must contain two normalized coordinates in [0, 1]")
