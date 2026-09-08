from cities_agent.actions import Action, ActionType, SafetyClass
from cities_agent.benchmark import StrategyBenchmark
from cities_agent.replay import ReplayEpisode, ReplayEvent, measure_replay
from cities_agent.simulator import MockCity


def test_replay_round_trip_and_determinism():
    city = MockCity()
    before = city.state
    action = Action(ActionType.ZONE, ("residential",), SafetyClass.REVERSIBLE)
    city.step([action])
    episode = ReplayEpisode("test", seed=0)
    episode.record(ReplayEvent(0, action, before, city.state, True, True, 0.95, "ok"))
    restored = ReplayEpisode.from_jsonl(episode.to_jsonl())
    final_a, accepted_a = episode.replay()
    final_b, accepted_b = restored.replay()
    assert restored.actions == episode.actions
    assert accepted_a == accepted_b == (True,)
    assert final_a.to_dict() == final_b.to_dict()
    assert measure_replay(restored).population_delta == 25


def test_replay_rejects_noncontiguous_events():
    episode = ReplayEpisode("bad")
    action = Action(ActionType.OBSERVE)
    try:
        episode.record(ReplayEvent(1, action))
    except ValueError as exc:
        assert "contiguous" in str(exc)
    else:
        raise AssertionError("Expected contiguous-index validation")


def test_benchmark_compares_strategies():
    benchmark = StrategyBenchmark()
    runs = benchmark.run({
        "residential": lambda city: (Action(ActionType.ZONE, ("residential",), SafetyClass.REVERSIBLE),),
        "observe": lambda city: (Action(ActionType.OBSERVE),),
    }, seeds=(0, 1, 2))
    summaries = {x.strategy: x for x in benchmark.summarize(runs)}
    assert summaries["residential"].runs == 3
    assert summaries["residential"].acceptance_rate == 1.0
    assert summaries["residential"].mean_population_delta > summaries["observe"].mean_population_delta
