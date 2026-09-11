from cities_agent.budget_control import BudgetControlProfile
from cities_agent.calibration import CalibrationError
from cities_agent.calibration_profile import profile_from_anchors
from cities_agent.live import LivePilot
from cities_agent.live_profile import LiveGameProfile, profile_from_calibration
from cities_agent.perception import Observation
from cities_agent.state_parser import profile_from_regions
from cities_agent.ui_evidence import UiEvidenceRule


def observation(width=1920, height=1080):
    from PIL import Image
    return Observation(Image.new("RGB", (width, height)), width, height)


def test_live_profile_unifies_matching_resolution_contracts():
    obs = observation()
    calibration = profile_from_anchors("cs-default", obs, {"zone:residential": (0.1, 0.1)})
    state = profile_from_regions(1920, 1080, {"hud": (0, 0, 1, 1)})
    profile = profile_from_calibration(
        calibration,
        state,
        ui_rules=(UiEvidenceRule("residential", "zone", "tool", (0, 0, 0.5, 1), ("residential",)),),
        budget=BudgetControlProfile(category_anchors={"electricity": "zone:residential"}),
    )
    profile.validate_observation(obs)
    assert profile.name == "cs-default"
    assert profile.ui_evidence_configured()
    assert profile.compiler().mapper.calibration == calibration.calibration


def test_live_profile_rejects_resolution_mismatch():
    obs = observation()
    calibration = profile_from_anchors("cs-default", obs, {"zone:residential": (0.1, 0.1)})
    state = profile_from_regions(1280, 720, {"hud": (0, 0, 1, 1)})
    try:
        profile_from_calibration(calibration, state)
    except ValueError as exc:
        assert "same resolution" in str(exc)
    else:
        raise AssertionError("Expected mismatched profiles to be rejected")


def test_live_profile_rejects_observation_resolution_mismatch():
    obs = observation()
    calibration = profile_from_anchors("cs-default", obs, {"zone:residential": (0.1, 0.1)})
    state = profile_from_regions(1920, 1080, {"hud": (0, 0, 1, 1)})
    profile = LiveGameProfile(calibration, state)
    try:
        profile.validate_observation(observation(1280, 720))
    except CalibrationError as exc:
        assert "expects 1920x1080" in str(exc)
    else:
        raise AssertionError("Expected observation mismatch to be rejected")


def test_live_pilot_set_profile_installs_calibration_compiler_reader_and_ui_verifier():
    class FakePilot:
        def __init__(self):
            self.calibration = None

        def set_calibration(self, calibration, obs):
            self.calibration = (calibration, obs.width, obs.height)

    class FakeController:
        def emergency_stop(self):
            pass

    obs = observation()
    calibration = profile_from_anchors("cs-default", obs, {"zone:residential": (0.1, 0.1)})
    state = profile_from_regions(1920, 1080, {"hud": (0, 0, 1, 1)})
    profile = profile_from_calibration(
        calibration,
        state,
        ui_rules=(UiEvidenceRule("residential", "zone", "tool", (0, 0, 0.5, 1), ("residential",)),),
    )
    pilot = FakePilot()
    live = LivePilot(
        observer=None,
        state_reader=lambda _: None,
        intent_provider=lambda *_: None,
        controller=FakeController(),
        pilot=pilot,
    )

    live.set_profile(profile, obs)

    assert live.profile is profile
    assert pilot.calibration[0] == calibration.calibration
    assert live.compiler is not None
    assert live.compiler.mapper.calibration == calibration.calibration
    assert live.state_reader(obs).timestamp is None
    assert live.verifier.ui_evidence.rules == profile.ui_rules
