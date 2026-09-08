from dataclasses import dataclass
from .ocr import OcrEngine
from .perception import Observation
from .state import CityState

@dataclass
class StateParser:
    ocr: OcrEngine

    def parse(self, observation: Observation) -> CityState:
        top = observation.screenshot.crop(observation.ui_regions["top_bar"].box)
        text = self.ocr.text(self.ocr_prepare(top))
        # This is deliberately conservative: until exact UI coordinates are calibrated,
        # don't assign uncertain OCR to game state.
        return CityState()

    def ocr_prepare(self, image):
        from PIL import ImageOps
        return ImageOps.autocontrast(ImageOps.grayscale(image))
