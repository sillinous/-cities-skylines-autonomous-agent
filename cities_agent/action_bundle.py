from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .actions import Action


class BundlePhase(str, Enum):
    PREPARE = "prepare"
    CONFIRM = "confirm"
    EFFECT = "effect"


@dataclass(frozen=True)
class ActionBundle:
    """A semantic intent's ordered execution transaction.

    PREPARE and CONFIRM actions establish UI context and require explicit UI
    evidence. EFFECT actions mutate the city and require deterministic state
    verification. The bundle itself carries no execution authority.
    """

    intent_kind: str
    actions: tuple[Action, ...]

    def __post_init__(self) -> None:
        if not self.actions:
            raise ValueError("ActionBundle requires at least one action")
        phases = [action.meta("phase") or BundlePhase.EFFECT.value for action in self.actions]
        if phases[-1] != BundlePhase.EFFECT.value:
            raise ValueError("ActionBundle must end with an effect action")
        if any(phase == BundlePhase.EFFECT.value for phase in phases[:-1]):
            raise ValueError("Effect action must be last in an ActionBundle")

    @property
    def pending(self) -> tuple[Action, ...]:
        return self.actions

    @property
    def effect(self) -> Action:
        return self.actions[-1]

    @property
    def preparation(self) -> tuple[Action, ...]:
        return self.actions[:-1]

    def phases(self) -> tuple[str, ...]:
        return tuple(action.meta("phase") or BundlePhase.EFFECT.value for action in self.actions)

    def validate(self) -> None:
        for index, action in enumerate(self.actions):
            phase = action.meta("phase") or BundlePhase.EFFECT.value
            if index < len(self.actions) - 1 and phase == BundlePhase.EFFECT.value:
                raise ValueError("Non-final bundle action cannot be an effect")
            if index == len(self.actions) - 1 and phase != BundlePhase.EFFECT.value:
                raise ValueError("Final bundle action must be an effect")
