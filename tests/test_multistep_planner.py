from cities_agent.planner import MultiStepPlanner
from cities_agent.policy import SafetyPolicy
from cities_agent.simulator import MockCity
from cities_agent.state import CityState
from cities_agent.strategic_manager import StrategicManager


def manager():
    return StrategicManager(policy=SafetyPolicy(allow_input=True, allow_reversible=True, max_actions_per_cycle=3))


def test_multistep_plan_has_steps_and_positive_value():
    m = manager()
    p = MultiStepPlanner(m, max_depth=3).search(MockCity().state, MockCity())
    assert p.valid
    assert p.steps
    assert len(p.actions) == len(p.steps)
    assert p.score > 0


def test_plan_step_invalidates_on_state_divergence():
    m = manager()
    city = MockCity()
    p = MultiStepPlanner(m, max_depth=2).search(city.state, city)
    assert p.steps
    planner = MultiStepPlanner(m)
    assert planner.validate_step(p.steps[0], p.steps[0].expected_state)
    observed = CityState(**p.steps[0].expected_state.to_dict())
    observed.money = (observed.money or 0) - 10_000
    assert not planner.validate_step(p.steps[0], observed)
    assert any(e.event == "plan_invalidated" for e in m.audit.events)


def test_replan_records_event():
    m = manager()
    city = MockCity()
    planner = MultiStepPlanner(m, max_depth=2)
    first = planner.search(city.state, city)
    changed = CityState(**city.state.to_dict())
    changed.residential_demand = 10
    planner.replan(changed, first, city)
    assert any(e.event == "replan" for e in m.audit.events)
