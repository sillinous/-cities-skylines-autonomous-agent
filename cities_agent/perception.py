from __future__ import annotations

from dataclasses import dataclass, field

import mss
from PIL import Image, ImageOps

from .ui_profile import CitiesSkylinesUiProfile


@dataclass
class UiRegion:
    name: str
    box: tuple[int, int, int, int]


@dataclass
class Observation:
    screenshot: Image.Image
    width: int
    height: int
    ui_regions: dict[str, UiRegion] = field(default_factory=dict)


class ScreenObserver:
    def __init__(self, profile: CitiesSkylinesUiProfile | None = None):
        self.profile = profile or CitiesSkylinesUiProfile()
        self.profile.validate()

    def capture(self) -> Observation:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            raw = sct.grab(monitor)
            image = Image.frombytes("RGB", raw.size, raw.rgb)
        regions = {
            name: UiRegion(name, self._scale_box(spec.box, image.width, image.height))
            for name, spec in self.profile.regions.items()
        }
        return Observation(image, image.width, image.height, regions)

    @staticmethod
    def _scale_box(box, width, height):
        x1, y1, x2, y2 = box
        return (round(x1 * width), round(y1 * height), round(x2 * width), round(y2 * height))

    def crop(self, observation: Observation, region: str) -> Image.Image:
        return observation.screenshot.crop(observation.ui_regions[region].box)

    def save_debug(self, observation: Observation, path="debug-screen.png"):
        observation.screenshot.save(path)

    def prepare_for_ocr(self, image: Image.Image) -> Image.Image:
        return ImageOps.autocontrast(ImageOps.grayscale(image))
