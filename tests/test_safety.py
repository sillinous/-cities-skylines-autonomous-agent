from cities_agent.actions import Action, ActionType, SafetyClass
from cities_agent.policy import SafetyPolicy


def test_input_disabled_by_default():
    ok, _ = SafetyPolicy().authorize(Action(ActionType.CLICK, (1, 2), SafetyClass.REVERSIBLE))
    assert not ok


def test_destructive_requires_explicit_permission():
    action = Action(ActionType.BULLDOZE, safety=SafetyClass.DESTRUCTIVE)
    ok, _ = SafetyPolicy(allow_input=True, allow_reversible=True).authorize(action)
    assert not ok


def test_read_only_is_allowed_when_input_disabled():
    ok, _ = SafetyPolicy().authorize(Action(ActionType.OBSERVE))
    assert ok
