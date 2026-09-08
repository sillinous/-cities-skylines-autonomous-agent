import pytest

from cities_agent.intent import Intent, IntentKind
from cities_agent.intent_validation import validate_intent


def test_zone_requires_target_and_point():
    with pytest.raises(ValueError, match="requires target"):
        validate_intent(Intent(IntentKind.ZONE, point=(0.5, 0.5)))


def test_construct_requires_end_point():
    with pytest.raises(ValueError, match="requires point and end"):
        validate_intent(Intent(IntentKind.CONSTRUCT, target="road", point=(0.2, 0.2)))


def test_budget_requires_integer_percentage():
    with pytest.raises(ValueError, match="integer percentage"):
        validate_intent(Intent(IntentKind.BUDGET, target="electricity", value=100.5))


def test_valid_budget_intent_passes():
    validate_intent(Intent(IntentKind.BUDGET, target="electricity", value=125))
