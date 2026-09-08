from __future__ import annotations

from .intent import Intent, IntentKind


def validate_intent(intent: Intent, min_confidence: float = 0.80) -> None:
    """Validate semantic intent shape before it can reach the action compiler."""
    intent.validate(min_confidence=min_confidence)
    required_target = {IntentKind.ZONE, IntentKind.UTILITY, IntentKind.SERVICE, IntentKind.BUDGET}
    if intent.kind in required_target and not intent.target.strip():
        raise ValueError(f"{intent.kind.value} intent requires target")
    if intent.kind in {IntentKind.ZONE, IntentKind.UTILITY, IntentKind.SERVICE, IntentKind.BULLDOZE, IntentKind.CAMERA} and intent.point is None:
        raise ValueError(f"{intent.kind.value} intent requires point")
    if intent.kind == IntentKind.CONSTRUCT and (intent.point is None or intent.end is None):
        raise ValueError("construct intent requires point and end")
    if intent.kind == IntentKind.BUDGET and intent.value is None:
        raise ValueError("budget intent requires value")
    if intent.kind == IntentKind.BUDGET and (not float(intent.value).is_integer() or not 0 <= intent.value <= 150):
        raise ValueError("budget value must be an integer percentage between 0 and 150")
