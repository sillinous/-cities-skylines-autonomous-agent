from __future__ import annotations

import re
from dataclasses import dataclass

from .ocr import OcrEngine
from .perception import Observation
from .state import CityState


@dataclass
class StateParser:
    """Turn OCR text into normalized state without guessing missing values."""

    ocr: OcrEngine
    min_confidence: float = 0.70

    def parse(self, observation: Observation) -> CityState:
        texts: list[str] = []
        for name in ("top_bar", "bottom_bar", "right_panel"):
            region = observation.ui_regions.get(name)
            if region is None:
                continue
            image = observation.screenshot.crop(region.box)
            texts.append(self.ocr.text(self.ocr_prepare(image)))
        text = "\n".join(texts)
        return self.parse_text(text)

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

        income = self._labeled_number(text, r"(?:weekly\s+)?income")
        expenses = self._labeled_number(text, r"(?:weekly\s+)?expenses?")
        assign("weekly_income", income)
        assign("weekly_expenses", expenses)

        lowered = text.lower()
        if re.search(r"\b(?:paused|pause)\b", lowered):
            state.simulation_paused = True
            confidence["simulation_paused"] = 0.92
        elif re.search(r"\b(?:playing|play)\b", lowered):
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

        state.power_ok = self._utility_status(text, "power")
        state.water_ok = self._utility_status(text, "water")
        state.sewage_ok = self._utility_status(text, "sewage")
        for field in ("power_ok", "water_ok", "sewage_ok"):
            if getattr(state, field) is not None:
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
        patterns = [
            r"traffic[^\d-]*(-?\d+(?:\.\d+)?)\s*%",
            r"(-?\d+(?:\.\d+)?)\s*%[^\n]{0,20}traffic",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return float(match.group(1))
        return None

    @staticmethod
    def _demand(text: str, zone: str):
        pattern = rf"{zone}\s*(?:demand)?[^-+\d]*([-+]?\d+)\s*%?"
        match = re.search(pattern, text, re.I)
        return int(match.group(1)) if match else None

    @staticmethod
    def _labeled_number(text: str, label: str):
        pattern = rf"{label}\s*[:=]?\s*\$?\s*([+-]?[\d,]+)"
        match = re.search(pattern, text, re.I)
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
        results = []
        for line in text.splitlines():
            line = " ".join(line.split())
            if re.search(r"\b(warning|shortage|insufficient|not enough|unserved|problem)\b", line, re.I):
                results.append(line)
        return results

    def ocr_prepare(self, image):
        from PIL import ImageOps
        return ImageOps.autocontrast(ImageOps.grayscale(image))
