import re
from typing import Optional
import pytesseract
from PIL import Image

class OcrEngine:
    def __init__(self, lang="eng"):
        self.lang = lang

    def text(self, image: Image.Image) -> str:
        return pytesseract.image_to_string(image, config="--psm 6", lang=self.lang)

    def integer(self, text: str) -> Optional[int]:
        m = re.search(r"[-+]?\$?\s*([\d,]+)", text)
        return int(m.group(1).replace(",", "")) if m else None

    def percent(self, text: str) -> Optional[float]:
        m = re.search(r"(-?\d+(?:\.\d+)?)\s*%", text)
        return float(m.group(1)) if m else None
