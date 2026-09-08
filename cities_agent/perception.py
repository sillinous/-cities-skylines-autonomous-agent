from dataclasses import dataclass, field
import mss
from PIL import Image, ImageOps

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
    DEFAULT_REGIONS = {
        "top_bar": (0, 0, 1920, 90),
        "bottom_bar": (0, 900, 1920, 1080),
        "left_toolbar": (0, 0, 110, 1080),
        "right_panel": (1600, 0, 1920, 1080),
    }

    def capture(self) -> Observation:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            raw = sct.grab(monitor)
            image = Image.frombytes("RGB", raw.size, raw.rgb)
        regions = {n: UiRegion(n, self._scale_box(b, image.width, image.height))
                   for n, b in self.DEFAULT_REGIONS.items()}
        return Observation(image, image.width, image.height, regions)

    @staticmethod
    def _scale_box(box, width, height):
        sx, sy = width / 1920, height / 1080
        x1, y1, x2, y2 = box
        return (int(x1*sx), int(y1*sy), int(x2*sx), int(y2*sy))

    def crop(self, observation: Observation, region: str) -> Image.Image:
        return observation.screenshot.crop(observation.ui_regions[region].box)

    def save_debug(self, observation: Observation, path="debug-screen.png"):
        observation.screenshot.save(path)

    def prepare_for_ocr(self, image: Image.Image) -> Image.Image:
        return ImageOps.autocontrast(ImageOps.grayscale(image))
