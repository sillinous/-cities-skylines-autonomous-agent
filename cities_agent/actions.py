from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    OBSERVE = "observe"
    CAMERA = "camera"
    SELECT_TOOL = "select_tool"
    CLICK = "click"
    DRAG = "drag"
    KEY = "key"
    BUILD_ROAD = "build_road"
    ZONE = "zone"
    BULLDOZE = "bulldoze"
    UTILITY = "utility"
    SERVICE = "service"
    BUDGET = "budget"


class SafetyClass(str, Enum):
    READ_ONLY = "read_only"
    REVERSIBLE = "reversible"
    DESTRUCTIVE = "destructive"


@dataclass(frozen=True)
class Action:
    type: ActionType
    args: tuple[Any, ...] = ()
    safety: SafetyClass = SafetyClass.READ_ONLY
    expected_effect: str = ""
    preconditions: tuple[str, ...] = ()
    max_retries: int = 0
    timeout_seconds: float = 3.0
    # Stable, serializable semantic facts supplied by the compiler.  This is
    # intentionally last so existing positional construction remains valid.
    metadata: tuple[tuple[str, str], ...] = ()

    @property
    def name(self) -> str:
        return self.type.value

    @property
    def destructive(self) -> bool:
        return self.safety == SafetyClass.DESTRUCTIVE

    def meta(self, key: str, default: str | None = None) -> str | None:
        """Return one compiler-supplied semantic metadata value."""
        return dict(self.metadata).get(key, default)


@dataclass
class ActionResult:
    action: Action
    executed: bool
    verified: bool = False
    reason: str = ""
    attempts: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
