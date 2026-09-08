from cities_agent.actions import SafetyClass
from cities_agent.intent import Intent, IntentKind
from cities_agent.policy import SafetyPolicy
from cities_agent.vision_planner import VisionIntentPlanner


def test_low_confidence_intent_is_rejected():
    planner = VisionIntentPlanner(SafetyPolicy(allow_input=True, allow_reversible=True))
    decision = planner.approve([Intent(IntentKind.ZONE, target="residential", confidence=0.5)])
    assert decision.selected is None
    assert "confidence" in decision.candidates[0].reason.lower()


def test_reversible_intent_can_pass_policy():
    planner = VisionIntentPlanner(SafetyPolicy(allow_input=True, allow_reversible=True))
    decision = planner.approve([Intent(IntentKind.ZONE, target="residential", confidence=0.95)])
    assert decision.selected is not None
    assert decision.selected.actions[0].safety == SafetyClass.REVERSIBLE


def test_destructive_intent_remains_blocked_without_explicit_permission():
    planner = VisionIntentPlanner(SafetyPolicy(allow_input=True, allow_reversible=True))
    decision = planner.approve([Intent(IntentKind.BULLDOZE, point=(0.5, 0.5), confidence=0.99)])
    assert decision.selected is None
    assert "destructive" in decision.candidates[0].reason.lower()
