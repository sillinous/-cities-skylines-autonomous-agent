from dataclasses import dataclass, field

from .actions import Action
from .perception import Observation
from .state import CityState
from .strategic_manager import Candidate, StrategicManager


@dataclass
class Plan:
    actions: list[Action]
    rationale: str
    candidates: list[Candidate] = field(default_factory=list)


class SafeStarterPlanner:
    """Compatibility facade over the deterministic strategic manager."""

    def __init__(self, manager: StrategicManager | None = None):
        self.manager = manager or StrategicManager()

    def plan(self, observation: Observation, state: CityState | None = None) -> Plan:
        if state is None:
            return Plan([], "Observation-only mode; normalized city state is not available.")
        decision = self.manager.plan(state)
        actions = [decision.action] if decision.action is not None else []
        return Plan(actions, decision.rationale, decision.candidates)
