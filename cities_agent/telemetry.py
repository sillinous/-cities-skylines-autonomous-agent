from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .actions import Action
from .state import CityState


@dataclass(frozen=True)
class TelemetryEvent:
    """Append-only operational event suitable for long-running agent runs."""

    sequence: int
    timestamp: float
    event: str
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TelemetryLog:
    """In-memory telemetry with optional JSONL persistence.

    Persistence is append-only from the caller's perspective. Telemetry never
    grants execution authority and is safe to use while input is disabled.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else None
        self.events: list[TelemetryEvent] = []

    def record(self, event: str, detail: str = "", **metadata: Any) -> TelemetryEvent:
        item = TelemetryEvent(len(self.events), time.time(), event, detail, metadata)
        self.events.append(item)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(item.to_dict(), sort_keys=True) + "\n")
        return item

    def extend(self, events: Iterable[TelemetryEvent]) -> None:
        for event in events:
            if event.sequence != len(self.events):
                raise ValueError("Telemetry sequences must be contiguous and zero-based.")
            self.events.append(event)

    def save(self, path: str | Path | None = None) -> None:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("A telemetry path is required.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "".join(json.dumps(e.to_dict(), sort_keys=True) + "\n" for e in self.events),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "TelemetryLog":
        target = Path(path)
        log = cls(target)
        if not target.exists():
            return log
        for line in target.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            event = TelemetryEvent(
                int(data["sequence"]), float(data["timestamp"]), str(data["event"]),
                str(data.get("detail", "")), dict(data.get("metadata", {})),
            )
            if event.sequence != len(log.events):
                raise ValueError("Telemetry sequences must be contiguous and zero-based.")
            log.events.append(event)
        return log

    def clear(self) -> None:
        self.events.clear()
        if self.path is not None and self.path.exists():
            self.path.unlink()


def state_summary(state: CityState | None) -> dict[str, Any]:
    if state is None:
        return {}
    return {
        "money": state.money,
        "population": state.population,
        "traffic_percent": state.traffic_percent,
        "demands": {
            "residential": state.residential_demand,
            "commercial": state.commercial_demand,
            "industrial": state.industrial_demand,
        },
        "utilities": {
            "power": state.power_ok,
            "water": state.water_ok,
            "sewage": state.sewage_ok,
        },
        "warnings": list(state.warnings),
    }


def record_action(telemetry: TelemetryLog, action: Action, *, state: CityState | None = None) -> None:
    telemetry.record("action", action.name, action=action.name, safety=action.safety.value, state=state_summary(state))
