from dataclasses import dataclass
from .control import Action
from .perception import Observation
from .state import CityState

@dataclass
class Plan:
    actions: list[Action]
    rationale: str

class SafeStarterPlanner:
    def plan(self, observation: Observation, state: CityState | None = None) -> Plan:
        return Plan([], "Observation-only mode; no game action requested.")
