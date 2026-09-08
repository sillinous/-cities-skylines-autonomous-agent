from __future__ import annotations

import re
from dataclasses import dataclass

from .ocr import OcrEngine
from .perception import Observation
from .state import CityState


@dataclass(frozen=True)
class StateFieldRegion:
    """Normalized screen region containing one state field."""

    name: str
    box: tuple[float, float, float, float]

    def pixels(self, observation: Observation) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = self.box
        if len(self.box) != 4 or any(not 0 <= value <= 1 for value in self.box):
            raise ValueError(f"Invalid normalized region for {self.name}.")
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"Region '{self.name}' must have positive area.")
        return (round(x1 * observation.width), round(y1 * observation.height),
                round(x2 * observation.width), round(y2 * observation.height))


@dataclass(frozen=True)
class StateParserProfile:
    """Explicit OCR profile for a fixed game-window resolution."""

    width: int
    height: int
    regions: dict[str, StateFieldRegion]

    def validate(self, observation: Observation) -> None:
        if (observation.width, observation.height) != (self.width, self.height):
            raise ValueError(
                f"State parser profile expects {self.width}x{self.height}, "
                f"got {observation.width}x{observation.height}."
            )


@dataclass
class StateParser:
    """Turn calibrated OCR text into normalized state without guessing."""

    ocr: OcrEngine
    min_confidence: float = 0.70
    profile: StateParserProfile | None = None

    def parse(self, observation: Observation) -> CityState:
        if self.profile is not None:
            self.profile.validate(observation)
            texts = []
            for region in self.profile.regions.values():
                image = observation.screenshot.crop(region.pixels(observation))
                texts.append(self.ocr.text(self.ocr_prepare(image)))
            return self.parse_text("\n".join(texts))

        texts: list[str] = []
        for name in ("top_bar", "bottom_bar", "right_panel"):
            region = observation.ui_regions.get(name)
            if region is None:
                continue
            image = observation.screenshot.crop(region.box)
            texts.append(self.ocr.text(self.ocr_prepare(image)))
        return self.parse_text("\n".join(texts))

    def parse_text(self, text: str) -> CityState:
        state = CityState()
        confidence: dict[str, float] = {}

        def assign(field: str, value, score: float = 0.90):
            if value is not None and score >= self.min_confidence:
                setattr(state, field, value)
                confidence[field] = score

        assign("money", self._money(text))
        assign("population", self._population(text))
        assign("traffic_percent", self._traffic(text))
        assign("residential_demand", self._demand(text, "residential"))
        assign("commercial_demand", self._demand(text, "commercial"))
        assign("industrial_demand", self._demand(text, "industrial"))
        assign("weekly_income", self._labeled_number(text, r"(?:weekly\s+)?income"))
        assign("weekly_expenses", self._labeled_number(text, r"(?:weekly\s+)?expenses?"))

        lowered = text.lower()
        if re.search(r"\b(?:paused|pause)\b", lowered):
            state.simulation_paused = True
            confidence["simulation_paused"] = 0.92
        elif re.search(r"\b(?:playing|play|running)\b", lowered):
            state.simulation_paused = False
            confidence["simulation_paused"] = 0.82

        speed = re.search(r"\bx\s*([1-3])\b|speed\s*[:=]?\s*([1-3])", lowered)
        if speed:
            state.simulation_speed = int(next(g for g in speed.groups() if g))
            confidence["simulation_speed"] = 0.82

        warnings = tuple(dict.fromkeys(self._warnings(text)))
        state.warnings = warnings
        if warnings:
            confidence["warnings"] = 0.88

        for field, utility in (("power_ok", "power"), ("water_ok", "water"), ("sewage_ok", "sewage")):
            value = self._utility_status(text, utility)
            if value is not None:
                setattr(state, field, value)
                confidence[field] = 0.86

        state.confidence = confidence
        return state

    @staticmethod
    def _money(text: str):
        return StateParser._labeled_number(text, r"(?:money|cash|funds|balance)")

    @staticmethod
    def _population(text: str):
        return StateParser._labeled_number(text, r"population")

    @staticmethod
    def _traffic(text: str):
        for pattern in (r"traffic[^\d-]*(-?\d+(?:\.\d+)?)\s*%", r"(-?\d+(?:\.\d+)?)\s*%[^\n]{0,20}traffic"):
            match = re.search(pattern, text, re.I)
            if match:
                return float(match.group(1))
        return None

    @staticmethod
    def _demand(text: str, zone: str):
        match = re.search(rf"{zone}\s*(?:demand)?[^-+\d]*([-+]?\d+)\s*%?", text, re.I)
        return int(match.group(1)) if match else None

    @staticmethod
    def _labeled_number(text: str, label: str):
        match = re.search(rf"{label}\s*[:=]?\s*\$?\s*([+-]?[\d,]+)", text, re.I)
        return int(match.group(1).replace(",", "")) if match else None

    @staticmethod
    def _utility_status(text: str, utility: str):
        lowered = text.lower()
        bad = rf"{utility}[^\n]{{0,30}}(?:shortage|insufficient|out|failure|not enough|unserved)"
        good = rf"{utility}[^\n]{{0,30}}(?:ok|adequate|sufficient|capacity)"
        if re.search(bad, lowered):
            return False
        if re.search(good, lowered):
            return True
        return None

    @staticmethod
    def _warnings(text: str) -> list[str]:
        return [
            " ".join(line.split())
            for line in text.splitlines()
            if re.search(r"\b(warning|shortage|insufficient|not enough|unserved|problem)\b", line, re.I)
        ]

    def ocr_prepare(self, image):
        from PIL import ImageOps
        return ImageOps.autocontrast(ImageOps.grayscale(image))


def profile_from_regions(width: int, height: int, regions: dict[str, tuple[float, float, float, float]]) -> StateParserProfile:
    if width <= 0 or height <= 0:
        raise ValueError("Profile resolution must be positive.")
    parsed = {name: StateFieldRegion(name, tuple(box)) for name, box in regions.items()}
    for region in parsed.values():
        if len(region.box) != 4 or any(not 0 <= value <= 1 for value in region.box):
            raise ValueError(f"Region '{region.name}' must use normalized coordinates in [0, 1].")
        if region.box[0] >= region.box[2] or region.box[1] >= region.box[3]:
            raise ValueError(f"Region '{region.name}' must have positive area.")
    return StateParserProfile(width, height, parsed)
