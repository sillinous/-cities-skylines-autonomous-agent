import pytest

from cities_agent.action_bundle import ActionBundle, BundlePhase
from cities_agent.actions import Action, ActionType, SafetyClass


def action(name, phase):
    return Action(
        ActionType.CLICK,
        {"x": 1, "y": 1},
        SafetyClass.REVERSIBLE,
        name=name,
        metadata=(("phase", phase), ("semantic_kind", "zone")),
    )


def test_bundle_requires_effect_last():
    bundle = ActionBundle("zone", (action("tool", BundlePhase.PREPARE.value), action("effect", BundlePhase.EFFECT.value)))
    assert bundle.preparation[0].name == "tool"
    assert bundle.effect.name == "effect"
    assert bundle.phases() == ("prepare", "effect")


def test_bundle_rejects_effect_before_final_action():
    with pytest.raises(ValueError, match="Effect action must be last"):
        ActionBundle("zone", (action("effect", "effect"), action("confirm", "confirm")))


def test_bundle_rejects_non_effect_final_action():
    with pytest.raises(ValueError, match="end with an effect"):
        ActionBundle("zone", (action("tool", "prepare"), action("confirm", "confirm")))
