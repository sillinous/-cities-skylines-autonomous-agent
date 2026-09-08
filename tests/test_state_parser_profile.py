from PIL import Image

from cities_agent.ocr import OcrEngine
from cities_agent.perception import Observation
from cities_agent.state_parser import StateParser, profile_from_regions


class FakeOCR(OcrEngine):
    def text(self, image):
        return "Money: $12,345 Population: 678 Traffic 91% Residential 25% Commercial -10% Industrial 5% Paused Power adequate Water sufficient Sewage shortage"


def test_profile_parses_calibrated_state():
    profile = profile_from_regions(1920, 1080, {"hud": (0.0, 0.0, 1.0, 1.0)})
    parser = StateParser(FakeOCR(), profile=profile)
    observation = Observation(Image.new("RGB", (1920, 1080)), 1920, 1080)
    state = parser.parse(observation)
    assert state.money == 12345
    assert state.population == 678
    assert state.traffic_percent == 91.0
    assert state.simulation_paused is True
    assert state.power_ok is True
    assert state.water_ok is True
    assert state.sewage_ok is False
    assert state.confidence_for("money") >= 0.8


def test_profile_rejects_resolution_mismatch():
    profile = profile_from_regions(1920, 1080, {"hud": (0.0, 0.0, 1.0, 1.0)})
    parser = StateParser(FakeOCR(), profile=profile)
    observation = Observation(Image.new("RGB", (1280, 720)), 1280, 720)
    try:
        parser.parse(observation)
    except ValueError as exc:
        assert "expects 1920x1080" in str(exc)
    else:
        raise AssertionError("Expected resolution mismatch to be rejected")
