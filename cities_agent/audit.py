from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    timestamp: str
    event: str
    detail: str = ""
    metadata: dict[str, Any] | None = None


class AuditLog:
    def __init__(self):
        self.events: list[AuditEvent] = []

    def record(self, event: str, detail: str = "", **metadata):
        self.events.append(
            AuditEvent(
                datetime.now(timezone.utc).isoformat(),
                event,
                detail,
                metadata or None,
            )
        )

    def clear(self):
        self.events.clear()
