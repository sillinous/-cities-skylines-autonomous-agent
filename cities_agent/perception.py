from dataclasses import dataclass
import mss
from PIL import Image

@dataclass
class Observation:
    screenshot: Image.Image
    width: int
    height: int

class ScreenObserver:
    def capture(self) -> Observation:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            raw = sct.grab(monitor)
            image = Image.frombytes("RGB", raw.size, raw.rgb)
            return Observation(image, raw.width, raw.height)

    def save_debug(self, observation: Observation, path: str = "debug-screen.png"):
        observation.screenshot.save(path)
