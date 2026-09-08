from cities_agent.actions import Action, ActionResult, ActionType, SafetyClass
from cities_agent.audit import AuditLog
from cities_agent.goals import GoalType
from cities_agent.policy import SafetyPolicy
from cities_agent.recovery import RecoveryController, RecoveryState
from cities_agent.simulator import MockCity
from cities_agent.state import CityState
from cities_agent.strategic_manager import StrategicManager


def test_high_residential_demand_creates_and_selects_safe_candidate():
    manager = StrategicManager(SafetyPolicy(allow_input=True, allow_reversible=True))
    state = CityState(money=20_000, population=100, weekly_income=1_000,
                      residential_demand=80, commercial_demand=10, industrial_demand=10,
                      traffic_percent=80.0)

    decision = manager.plan(state, MockCity())

    assert decision.action is not None
    assert decision.action.type == ActionType.ZONE
    assert decision.action.args == ("residential",)
    assert decision.candidates[0].score > 0


def test_low_traffic_does_not_trigger_reckless_road_action():
    manager = StrategicManager(SafetyPolicy(allow_input=True, allow_reversible=True))
    state = CityState(money=20_000, population=1_900, weekly_income=1_000,
                      residential_demand=10, commercial_demand=10, industrial_demand=10,
                      traffic_percent=20.0)

    decision = manager.plan(state, MockCity())

    assert decision.action is None
    assert all(c.action.type != ActionType.BUILD_ROAD for c in decision.candidates)


def test_low_cash_does_not_get_overridden_by_demand():
    manager = StrategicManager(SafetyPolicy(allow_input=True, allow_reversible=True))
    state = CityState(money=1_000, population=100, weekly_income=100,
                      residential_demand=90, commercial_demand=10, industrial_demand=10,
                      traffic_percent=80.0)

    decision = manager.plan(state, MockCity())

    assert decision.action is None


def test_destructive_action_is_blocked_by_policy():
    policy = SafetyPolicy(allow_input=True, allow_reversible=True, allow_destructive=False)
    manager = StrategicManager(policy)
    destructive = Action(ActionType.BULLDOZE, (1, 2), SafetyClass.DESTRUCTIVE)

    assert policy.authorize(destructive) == (False, "Destructive input is disabled by safety policy.")
    assert manager.evaluate(CityState(money=10_000), destructive).score == float("-inf") is False


def test_failed_verification_enters_recovery_and_audit():
    audit = AuditLog()
    recovery = RecoveryController(max_retries=1)
    manager = StrategicManager(audit=audit, recovery=recovery)
    action = Action(ActionType.ZONE, ("residential",), SafetyClass.REVERSIBLE)

    manager.record_execution(ActionResult(action=action, executed=True, verified=False, reason="No visible effect."))

    assert recovery.state == RecoveryState.RETRYING
    assert recovery.retries == 1
    assert any(event.event == "recovery" for event in audit.events)


def test_hard_warning_forces_observation():
    manager = StrategicManager()
    state = CityState(warnings=("Power outage",), residential_demand=90)

    decision = manager.plan(state)

    assert decision.action is not None
    assert decision.action.type == ActionType.OBSERVE
    assert manager.goals_for(state)[0].type == GoalType.AVOID_FAILURE


def test_audit_records_selected_plan():
    audit = AuditLog()
    manager = StrategicManager(SafetyPolicy(allow_input=True, allow_reversible=True), audit=audit)
    state = CityState(money=20_000, population=100, weekly_income=1_000,
                      residential_demand=80, commercial_demand=10, industrial_demand=10,
                      traffic_percent=80.0)

    manager.plan(state, MockCity())

    assert audit.events
    assert audit.events[-1].event == "plan"
