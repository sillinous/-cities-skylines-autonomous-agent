from cities_agent.calibration import CalibrationError
from cities_agent.calibration_profile import profile_from_anchors
from cities_agent.perception import Observation
from cities_agent.state import CityState
from cities_agent.windows import WindowInfo, WindowsGameWindow
from PIL import Image


def obs(width=1920, height=1080):
    return Observation(Image.new("RGB", (width, height)), width, height)


def test_calibration_profile_is_resolution_bound():
    profile = profile_from_anchors("default", obs(), {"road:road": (0.2, 0.8)})
    profile.validate_observation(obs())
    try:
        profile.validate_observation(obs(1280, 720))
    except CalibrationError:
        pass
    else:
        raise AssertionError("resolution mismatch must be rejected")


def test_calibration_profile_rejects_invalid_anchor():
    try:
        profile_from_anchors("bad", obs(), {"center": (1.1, 0.5)})
    except CalibrationError:
        pass
    else:
        raise AssertionError("invalid normalized anchor must be rejected")


def test_window_adapter_matches_case_insensitively():
    adapter = WindowsGameWindow()
    adapter.enumerate = lambda: (
        WindowInfo(1, "Notepad", True),
        WindowInfo(2, "Cities: Skylines", True),
    )
    assert adapter.find_game().handle == 2
    assert adapter.game_detected()
