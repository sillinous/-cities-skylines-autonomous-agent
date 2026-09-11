from cities_agent.live import LivePilot
from cities_agent.live_profile import LiveGameProfile
from cities_agent.calibration_profile import profile_from_anchors
from cities_agent.state_parser import profile_from_regions
from cities_agent.perception import Observation
from cities_agent.pilot import PilotGuard
from cities_agent.control import DryRunController
from cities_agent.intent import Intent
from PIL import Image


def obs(w=1920, h=1080):
    return Observation(Image.new("RGB", (w, h)), w, h)


def test_profile_installs_without_enabling_input():
    o = obs()
    cal = profile_from_anchors("test", o, {"zone:residential": (0.1, 0.1)})
    state = profile_from_regions(1920, 1080, {"hud": (0, 0, 1, 1)})
    profile = LiveGameProfile(cal, state)
    pilot = PilotGuard(dry_run=True)
    live = LivePilot(observer=lambda: None, state_reader=lambda _: None, intent_provider=lambda *_: None, controller=DryRunController(), pilot=pilot)
    live.set_profile(profile, o)
    assert live.compiler is not None
    assert pilot.config.dry_run is True
