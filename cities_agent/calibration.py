from __future__ import annotations

from dataclasses import dataclass

from .perception import Observation


@dataclass(frozen=True)
class Calibration:
    """Normalized coordinates for a game viewport.

    Coordinates are expressed as fractions of the captured screen, making
    them portable across supported resolutions. Concrete game adapters can
    populate named anchors after calibration instead of hard-coding pixels.
    """

    width: int
    height: int
    anchors: dict[str, tuple[float, float]]

    def pixel(self, name: str) -> tuple[int, int]:
        x, y = self.anchors[name]
        return round(x * self.width), round(y * self.height)


class CalibrationError(ValueError):
    pass


def calibrate(observation: Observation, anchors: dict[str, tuple[float, float]]) -> Calibration:
    for name, (x, y) in anchors.items():
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            raise CalibrationError(f"Anchor {name!r} must use normalized coordinates in [0, 1].")
    return Calibration(observation.width, observation.height, dict(anchors))
