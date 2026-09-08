from dataclasses import dataclass
from .control import Action
from .perception import Observation

@dataclass
class Plan:
    actions: list[Action]
    rationale: str

class SafeStarterPlanner:
    def plan(self, observation: Observation) -> Plan:
        return Plan([], "Observation-only mode; no game action requested.")
