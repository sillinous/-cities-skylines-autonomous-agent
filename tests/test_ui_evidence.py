from PIL import Image

from cities_agent.actions import Action, ActionType, SafetyClass
from cities_agent.perception import Observation
from cities_agent.ui_evidence import OcrUiEvidenceVerifier, UiEvidenceRule


class FakeOcr:
    def __init__(self, text):
        self._text = text

    def text(self, image):
        return self._text


def observation():
    image = Image.new("RGB", (1000, 500))
    return Observation(image, 1000, 500)


def action():
    return Action(
        ActionType.CLICK,
        (100, 100),
        SafetyClass.REVERSIBLE,
        metadata=(("semantic_kind", "zone"), ("target", "residential"), ("phase", "tool")),
    )


def test_ocr_ui_evidence_requires_profiled_token():
    verifier = OcrUiEvidenceVerifier(
        rules=(UiEvidenceRule("residential_tool", "zone", "tool", (0, 0, 0.5, 1), ("residential",)),),
        ocr=FakeOcr("Residential zone selected"),
    )
    result = verifier.verify(observation(), observation(), action())
    assert result.success
    assert result.confidence == 0.90


def test_ocr_ui_evidence_rejects_wrong_tool_text():
    verifier = OcrUiEvidenceVerifier(
        rules=(UiEvidenceRule("residential_tool", "zone", "tool", (0, 0, 0.5, 1), ("residential",)),),
        ocr=FakeOcr("Commercial zone selected"),
    )
    result = verifier.verify(observation(), observation(), action())
    assert not result.success
    assert result.confidence == 0.0


def test_missing_ui_profile_is_a_hard_failure():
    verifier = OcrUiEvidenceVerifier(ocr=FakeOcr("Residential zone selected"))
    result = verifier.verify(observation(), observation(), action())
    assert not result.success
    assert result.confidence == 0.0


def test_effect_phase_is_not_allowed_as_ui_evidence_rule():
    try:
        UiEvidenceRule("bad", "zone", "effect", (0, 0, 1, 1), ("residential",)).validate()
    except ValueError as exc:
        assert "final effects" in str(exc)
    else:
        raise AssertionError("effect rules must be rejected")
