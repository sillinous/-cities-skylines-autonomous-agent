from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .actions import Action
from .replay import action_from_dict, action_to_dict
from .state import CityState
from .telemetry import state_summary


@dataclass(frozen=True)
class Checkpoint:
    """Restart-safe logical checkpoint; it does not mutate or load a game save."""

    episode_id: str
    step: int
    state: CityState
    pending_actions: tuple[Action, ...] = ()
    planner_context: dict[str, Any] | None = None
    source: str = "agent"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "episode_id": self.episode_id,
            "step": self.step,
            "state": self.state.to_dict(),
            "pending_actions": [action_to_dict(a) for a in self.pending_actions],
            "planner_context": self.planner_context or {},
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        if int(data.get("version", 1)) != 1:
            raise ValueError("Unsupported checkpoint version.")
        raw = dict(data["state"])
        raw["warnings"] = tuple(raw.get("warnings", ()))
        raw["service_coverage"] = dict(raw.get("service_coverage", {}))
        raw["budgets"] = dict(raw.get("budgets", {}))
        raw["confidence"] = dict(raw.get("confidence", {}))
        return cls(
            str(data["episode_id"]), int(data["step"]), CityState(**raw),
            tuple(action_from_dict(a) for a in data.get("pending_actions", [])),
            dict(data.get("planner_context", {})), str(data.get("source", "agent")),
        )

    def summary(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "step": self.step,
            "pending_action_count": len(self.pending_actions),
            "state": state_summary(self.state),
            "source": self.source,
        }


class CheckpointStore:
    """Atomic-ish single-file checkpoint store with explicit versioning."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, checkpoint: Checkpoint) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(checkpoint.to_dict(), sort_keys=True, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def load(self) -> Checkpoint:
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        return Checkpoint.from_dict(json.loads(self.path.read_text(encoding="utf-8")))

    def exists(self) -> bool:
        return self.path.exists()

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
