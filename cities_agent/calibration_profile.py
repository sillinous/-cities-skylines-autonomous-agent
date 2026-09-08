from __future__ import annotations

from dataclasses import dataclass

from .calibration import Calibration, CalibrationError
from .perception import Observation


@dataclass(frozen=True)
class CalibrationProfile:
    """Named UI profile for a specific game-window resolution."""

    name: str
    calibration: Calibration

    def validate_observation(self, observation: Observation) -> None:
        if (observation.width, observation.height) != (
            self.calibration.width,
            self.calibration.height,
        ):
            raise CalibrationError(
                f"Profile '{self.name}' expects {self.calibration.width}x{self.calibration.height}, "
                f"got {observation.width}x{observation.height}."
            )


def profile_from_anchors(
    name: str,
    observation: Observation,
    anchors: dict[str, tuple[float, float]],
) -> CalibrationProfile:
    if not name.strip():
        raise CalibrationError("Calibration profile name must not be empty.")
    calibration = Calibration(observation.width, observation.height, dict(anchors))
    for anchor, point in calibration.anchors.items():
        if len(point) != 2 or any(not 0.0 <= value <= 1.0 for value in point):
            raise CalibrationError(f"Anchor '{anchor}' must use normalized coordinates in [0, 1].")
    return CalibrationProfile(name, calibration)
