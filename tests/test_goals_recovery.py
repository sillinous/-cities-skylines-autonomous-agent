from cities_agent.goals import Goal, GoalType
from cities_agent.recovery import RecoveryController, RecoveryState


def test_goal_validation():
    Goal(GoalType.GROW_POPULATION, priority=80, risk_tolerance=0.2)


def test_recovery_retries_then_fails():
    recovery = RecoveryController(max_retries=1)
    recovery.begin()
    assert recovery.verification_failed()
    assert recovery.state == RecoveryState.RETRYING
    assert not recovery.verification_failed()
    assert recovery.state == RecoveryState.FAILED


def test_recovery_success_resets():
    recovery = RecoveryController()
    recovery.begin()
    recovery.verified()
    assert recovery.state == RecoveryState.READY
    assert recovery.retries == 0
