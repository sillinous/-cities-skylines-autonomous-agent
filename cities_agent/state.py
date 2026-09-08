from dataclasses import dataclass, asdict, field
from typing import Optional


@dataclass
class CityState:
    """Normalized state shared by all supported game/UI adapters."""
    timestamp: Optional[float] = None
    simulation_paused: Optional[bool] = None
    simulation_speed: Optional[int] = None
    money: Optional[int] = None
    weekly_income: Optional[int] = None
    weekly_expenses: Optional[int] = None
    population: Optional[int] = None
    residential_demand: Optional[int] = None
    commercial_demand: Optional[int] = None
    industrial_demand: Optional[int] = None
    traffic_percent: Optional[float] = None
    power_ok: Optional[bool] = None
    water_ok: Optional[bool] = None
    sewage_ok: Optional[bool] = None
    service_coverage: dict[str, float] = field(default_factory=dict)
    budgets: dict[str, int] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    confidence: dict[str, float] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    def confidence_for(self, field_name: str) -> float:
        return self.confidence.get(field_name, 0.0)
