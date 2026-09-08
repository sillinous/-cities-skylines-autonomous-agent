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


@dataclass(frozen=True)
class PlacementSpec:
    """Calibrated placement for a tool that requires a world target."""
    tool_anchor: str
    point: tuple[float, float]
    safety: SafetyClass = SafetyClass.REVERSIBLE


class CitiesSkylinesActionMapper:
    """Map semantic intents to calibrated low-level input actions."""

    def __init__(self, calibration: Calibration):
        self.calibration = calibration

    def click_anchor(self, anchor: str, *, safety: SafetyClass = SafetyClass.REVERSIBLE) -> Action:
        x, y = self.calibration.pixel(anchor)
        return Action(ActionType.CLICK, (x, y), safety, expected_effect=f"Click calibrated anchor '{anchor}'.")

    def select_tool(self, anchor: str) -> Action:
        return self.click_anchor(anchor)

    def build_road(self, spec: BuildSpec) -> tuple[Action, ...]:
        self._validate_point(spec.start)
        self._validate_point(spec.end)
        x1, y1 = self._pixel(spec.start)
        x2, y2 = self._pixel(spec.end)
        return (
            self.select_tool(f"road:{spec.road_type}"),
            Action(ActionType.DRAG, (x1, y1, x2, y2), SafetyClass.REVERSIBLE, expected_effect="Draw the requested road segment."),
        )

    def zone(self, zone_type: str, point: tuple[float, float]) -> tuple[Action, ...]:
        return self.place(PlacementSpec(f"zone:{self._zone(zone_type)}", point))

    def utility(self, utility: str, point: tuple[float, float] | None = None) -> tuple[Action, ...]:
        utility = utility.lower().strip()
        if utility not in {"power", "water", "sewage"}:
            raise ValueError("utility must be power, water, or sewage")
        if point is None:
            raise ValueError("utility placement requires point")
        return self.place(PlacementSpec(f"utility:{utility}", point))

    def service(self, service: str, point: tuple[float, float] | None = None) -> tuple[Action, ...]:
        service = service.lower().strip()
        if not service:
            raise ValueError("service must not be empty")
        if point is None:
            raise ValueError("service placement requires point")
        return self.place(PlacementSpec(f"service:{service}", point))

    def place(self, spec: PlacementSpec) -> tuple[Action, ...]:
        self._validate_point(spec.point)
        x, y = self._pixel(spec.point)
        return (
            self.select_tool(spec.tool_anchor),
            Action(ActionType.CLICK, (x, y), spec.safety, expected_effect=f"Place {spec.tool_anchor} at calibrated world point."),
        )

    def bulldoze(self, point: tuple[float, float]) -> tuple[Action, ...]:
        self._validate_point(point)
        return (
            self.select_tool("bulldoze"),
            Action(ActionType.CLICK, self._pixel(point), SafetyClass.DESTRUCTIVE, expected_effect="Remove the targeted construction."),
        )

    def budget(self, category: str, percentage: int) -> tuple[Action, ...]:
        if not category.strip():
            raise ValueError("budget category must not be empty")
        if not 0 <= percentage <= 150:
            raise ValueError("budget percentage must be between 0 and 150")
        return (Action(ActionType.BUDGET, (category.lower().strip(), percentage), SafetyClass.REVERSIBLE, expected_effect=f"Set {category} budget to {percentage}% ."),)

    def _pixel(self, point: tuple[float, float]) -> tuple[int, int]:
        return round(point[0] * self.calibration.width), round(point[1] * self.calibration.height)

    @staticmethod
    def _zone(zone_type: str) -> str:
        normalized = zone_type.lower().strip()
        if normalized not in {"residential", "commercial", "industrial"}:
            raise ValueError("zone_type must be residential, commercial, or industrial")
        return normalized

    @staticmethod
    def _validate_point(point: tuple[float, float]) -> None:
        if len(point) != 2 or any(not 0.0 <= value <= 1.0 for value in point):
            raise ValueError("points must contain two normalized coordinates in [0, 1]")
