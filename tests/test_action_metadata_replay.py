from cities_agent.actions import Action, ActionType, SafetyClass
from cities_agent.replay import action_from_dict, action_to_dict


def test_action_metadata_round_trips_through_replay_serialization():
    action = Action(
        ActionType.CLICK,
        (100, 200),
        SafetyClass.REVERSIBLE,
        expected_effect="Place zone:residential at calibrated world point.",
        metadata=(("semantic_kind", "zone"), ("target", "residential"), ("phase", "effect")),
    )
    restored = action_from_dict(action_to_dict(action))
    assert restored == action
