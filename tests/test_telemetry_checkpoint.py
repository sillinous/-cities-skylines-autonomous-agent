from cities_agent.actions import Action, ActionType, SafetyClass
from cities_agent.checkpoint import Checkpoint, CheckpointStore
from cities_agent.state import CityState
from cities_agent.telemetry import TelemetryLog


def sample_state():
    return CityState(money=1234, population=456, power_ok=True, warnings=("test",))


def test_checkpoint_round_trip(tmp_path):
    action = Action(ActionType.ZONE, ("residential",), SafetyClass.REVERSIBLE)
    checkpoint = Checkpoint("episode-1", 7, sample_state(), (action,), {"goal": "grow"})
    store = CheckpointStore(tmp_path / "checkpoint.json")
    store.save(checkpoint)
    restored = store.load()
    assert restored == checkpoint
    assert restored.summary()["pending_action_count"] == 1


def test_checkpoint_store_replaces_previous_checkpoint(tmp_path):
    store = CheckpointStore(tmp_path / "checkpoint.json")
    store.save(Checkpoint("a", 1, sample_state()))
    store.save(Checkpoint("b", 2, sample_state()))
    assert store.load().episode_id == "b"
    store.clear()
    assert not store.exists()


def test_telemetry_persists_and_continues_sequence(tmp_path):
    path = tmp_path / "telemetry.jsonl"
    log = TelemetryLog(path)
    log.record("start", episode="x")
    log.record("stop", reason="verification")
    restored = TelemetryLog.load(path)
    assert [e.sequence for e in restored.events] == [0, 1]
    assert restored.events[1].metadata["reason"] == "verification"
