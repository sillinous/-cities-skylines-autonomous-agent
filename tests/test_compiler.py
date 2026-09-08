from cities_agent.action_mapping import BuildSpec
from cities_agent.calibration import Calibration
from cities_agent.compiler import IntentCompiler
from cities_agent.intent import Intent, IntentKind


def compiler():
    return IntentCompiler(Calibration(1920, 1080, {"road:road": (0.1, 0.1), "zone:residential": (0.2, 0.2), "utility:power": (0.3, 0.3), "service:fire": (0.4, 0.4), "bulldoze": (0.5, 0.5)}))


def test_construct_compiles_to_tool_and_drag():
    result = compiler().compile(Intent(IntentKind.CONSTRUCT, target="road", point=(0.1, 0.2), end=(0.3, 0.4)))
    assert [action.name for action in result.actions] == ["select_tool", "drag"]
    assert result.actions[-1].args == (192, 216, 576, 432)


def test_zone_compiles_to_tool_and_click():
    result = compiler().compile(Intent(IntentKind.ZONE, target="residential", point=(0.25, 0.5)))
    assert [action.name for action in result.actions] == ["select_tool", "click"]
    assert result.actions[-1].args == (480, 540)


def test_low_confidence_is_rejected():
    result = compiler().compile(Intent(IntentKind.OBSERVE, confidence=0.79))
    assert result.actions == ()
    assert "confidence" in result.reason.lower()


def test_unsupported_target_is_rejected_without_dispatch():
    result = compiler().compile(Intent(IntentKind.ZONE, target="airport", point=(0.5, 0.5)))
    assert result.actions == ()
    assert result.reason
