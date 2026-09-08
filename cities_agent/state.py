from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class CityState:
    money: Optional[int] = None
    population: Optional[int] = None
    weekly_income: Optional[int] = None
    residential_demand: Optional[int] = None
    commercial_demand: Optional[int] = None
    industrial_demand: Optional[int] = None
    traffic_percent: Optional[float] = None
    power_ok: Optional[bool] = None
    water_ok: Optional[bool] = None
    sewage_ok: Optional[bool] = None
    warnings: tuple[str, ...] = ()

    def to_dict(self):
        return asdict(self)
