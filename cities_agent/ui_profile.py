from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RegionSpec:
    """Resolution-independent UI region expressed as normalized coordinates."""

    name: str
    box: tuple[float, float, float, float]

    def validate(self) -> None:
        x1, y1, x2, y2 = self.box
        if not (0.0 <= x1 < x2 <= 1.0 and 0.0 <= y1 < y2 <= 1.0):
            raise ValueError(f"Invalid normalized region {self.name!r}: {self.box!r}")


@dataclass(frozen=True)
class CitiesSkylinesUiProfile:
    """Conservative Cities: Skylines UI layout profile.

    These are broad capture regions, not click coordinates. Exact controls remain
    calibration-dependent so the agent never silently clicks an assumed location.
    """

    regions: dict[str, RegionSpec] = field(default_factory=lambda: {
        "top_bar": RegionSpec("top_bar", (0.0, 0.0, 1.0, 0.12)),
        "bottom_bar": RegionSpec("bottom_bar", (0.0, 0.82, 1.0, 1.0)),
        "left_toolbar": RegionSpec("left_toolbar", (0.0, 0.0, 0.10, 1.0)),
        "right_panel": RegionSpec("right_panel", (0.83, 0.0, 1.0, 1.0)),
    })

    def validate(self) -> None:
        for region in self.regions.values():
            region.validate()
