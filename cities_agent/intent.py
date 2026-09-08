from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .actions import Action


class IntentKind(str, Enum):
    OBSERVE = "observe"
    CONSTRUCT = "construct"
    ZONE = "zone"
    UTILITY = "utility"
    SERVICE = "service"
    BULLDOZE = "bulldoze"
    BUDGET = "budget"
    CAMERA = "camera"


@dataclass(frozen=True)
class Intent:
    """A semantic request that still requires deterministic validation/mapping."""

    kind: IntentKind
    target: str = ""
    point: tuple[float, float] | None = None
    end: tuple[float, float] | None = None
    value: float | None = None
    confidence: float = 1.0
    rationale: str = ""

    def validate(self, min_confidence: float = 0.80) -> None:
        if self.confidence < min_confidence:
            raise ValueError("Intent confidence is below the execution threshold.")
        for point in (self.point, self.end):
            if point is not None and (len(point) != 2 or any(not 0 <= x <= 1 for x in point)):
                raise ValueError("Intent coordinates must be normalized to [0, 1].")


@dataclass(frozen=True)
class IntentCandidate:
    intent: Intent
    actions: tuple[Action, ...]
    score: float
    approved: bool = False
    reason: str = ""
