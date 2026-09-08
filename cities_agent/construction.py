from __future__ import annotations

from dataclasses import dataclass

from .actions import Action, ActionType, SafetyClass


@dataclass(frozen=True)
class ConstructionIntent:
    """Game-independent construction intent.

    Coordinates are normalized to the captured screen. The intent describes
    what should happen; the mapper/controller decides how to dispatch it.
    """

    kind: str
    target: str = ""
    start: tuple[float, float] | None = None
    end: tuple[float, float] | None = None
    point: tuple[float, float] | None = None
    value: int | float | None = None


class ConstructionActions:
    """Create semantic actions with explicit safety and expected effects."""

    @staticmethod
    def road(start: tuple[float, float], end: tuple[float, float], road_type: str = "road") -> ConstructionIntent:
        return ConstructionIntent("road", road_type, start=start, end=end)

    @staticmethod
    def zone(zone_type: str, point: tuple[float, float]) -> ConstructionIntent:
        zone_type = zone_type.lower()
        if zone_type not in {"residential", "commercial", "industrial"}:
            raise ValueError("zone_type must be residential, commercial, or industrial")
        return ConstructionIntent("zone", zone_type, point=point)

    @staticmethod
    def utility(utility: str) -> Action:
        utility = utility.lower()
        if utility not in {"power", "water", "sewage"}:
            raise ValueError("utility must be power, water, or sewage")
        return Action(ActionType.UTILITY, (utility,), SafetyClass.REVERSIBLE,
                      expected_effect=f"Restore {utility} service.",
                      preconditions=(f"{utility}_ok == false",))

    @staticmethod
    def service(service: str) -> Action:
        if not service.strip():
            raise ValueError("service must not be empty")
        return Action(ActionType.SERVICE, (service.lower(),), SafetyClass.REVERSIBLE,
                      expected_effect=f"Improve {service} service coverage.")

    @staticmethod
    def bulldoze(point: tuple[float, float]) -> ConstructionIntent:
        return ConstructionIntent("bulldoze", point=point)

    @staticmethod
    def budget(category: str, value: int) -> Action:
        if value < 0:
            raise ValueError("budget value must be non-negative")
        return Action(ActionType.BUDGET, (category, value), SafetyClass.REVERSIBLE,
                      expected_effect=f"Set {category} budget to {value}%.")

    @staticmethod
    def as_action(intent: ConstructionIntent) -> Action:
        if intent.kind == "road":
            return Action(ActionType.BUILD_ROAD, (intent.target, intent.start, intent.end), SafetyClass.REVERSIBLE,
                          expected_effect="Build the requested road segment.")
        if intent.kind == "zone":
            return Action(ActionType.ZONE, (intent.target, intent.point), SafetyClass.REVERSIBLE,
                          expected_effect=f"Apply {intent.target} zoning at the requested location.")
        if intent.kind == "bulldoze":
            return Action(ActionType.BULLDOZE, (intent.point,), SafetyClass.DESTRUCTIVE,
                          expected_effect="Remove the targeted construction.")
        raise ValueError(f"Unsupported construction intent: {intent.kind}")
