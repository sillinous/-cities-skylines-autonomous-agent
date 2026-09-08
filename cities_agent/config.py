from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Config:
    enabled: bool = os.getenv("AGENT_ENABLE_INPUT", "0") == "1"
    loop_seconds: float = float(os.getenv("AGENT_LOOP_SECONDS", "2.0"))
    max_actions_per_cycle: int = int(os.getenv("AGENT_MAX_ACTIONS", "1"))
