from cities_agent.actions import ActionType, SafetyClass
from cities_agent.calibration import Calibration
from cities_agent.action_mapping import BuildSpec, CitiesSkylinesActionMapper
from cities_agent.construction import ConstructionActions


def test_semantic_construction_actions_have_explicit_safety():
    assert ConstructionActions.utility("power").safety == SafetyClass.REVERSIBLE
    assert ConstructionActions.bulldoze((0.5, 0.5)).kind == "bulldoze"
    assert ConstructionActions.as_action(ConstructionActions.zone("residential", (0.2, 0.3))).type == ActionType.ZONE


def test_mapper_converts_normalized_road_to_calibrated_input():
    calibration = Calibration(1920, 1080, {"road:road": (0.1, 0.2)})
    mapper = CitiesSkylinesActionMapper(calibration)
    actions = mapper.build_road(BuildSpec((0.25, 0.50), (0.75, 0.50)))
    assert actions[0].type == ActionType.SELECT_TOOL
    assert actions[0].args == (192, 216)
    assert actions[1].type == ActionType.DRAG
    assert actions[1].args == (480, 540, 1440, 540)
