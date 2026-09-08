from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from PIL import Image


@dataclass(frozen=True)
class VisionObservation:
    """Structured, game-agnostic visual evidence produced from a screenshot."""

    labels: tuple[str, ...] = ()
    text: tuple[str, ...] = ()
    regions: dict[str, tuple[int, int, int, int]] = field(default_factory=dict)
    confidence: dict[str, float] = field(default_factory=dict)

    def confidence_for(self, key: str) -> float:
        return self.confidence.get(key, 0.0)


class VisionBackend(Protocol):
    def analyze(self, image: Image.Image) -> VisionObservation: ...


class NullVisionBackend:
    """Safe default: no semantic visual claims are made."""

    def analyze(self, image: Image.Image) -> VisionObservation:
        return VisionObservation()


class VisionPerceptor:
    """Combine OCR/state extraction with an optional vision backend.

    The backend is intentionally injectable. A future local or remote vision
    model can implement VisionBackend without gaining authority to issue input.
    """

    def __init__(self, backend: VisionBackend | None = None):
        self.backend = backend or NullVisionBackend()

    def analyze(self, image: Image.Image) -> VisionObservation:
        return self.backend.analyze(image)
