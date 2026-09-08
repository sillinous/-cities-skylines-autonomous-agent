from cities_agent.calibration import Calibration
from cities_agent.camera import CameraNavigator, CameraPoint
from cities_agent.action_mapping import BuildSpec, CitiesSkylinesActionMapper
from cities_agent.actions import ActionType


def calibration():
    return Calibration(1920, 1080, {"viewport_center": (0.5, 0.5), "road": (0.1, 0.9)})


def test_camera_pan_is_resolution_calibrated():
    action = CameraNavigator(calibration()).pan(CameraPoint(0.25, 0.5), CameraPoint(0.75, 0.5))
    assert action.type == ActionType.DRAG
    assert action.args == (480, 540, 1440, 540)


def test_camera_zoom_and_rotation_are_typed():
    navigator = CameraNavigator(calibration())
    assert navigator.zoom("in", 2).args == ("pageup", 2)
    assert navigator.rotate("right", 1).args == ("e", 1)


def test_build_road_maps_to_tool_then_drag():
    mapper = CitiesSkylinesActionMapper(calibration())
    actions = mapper.build_road(BuildSpec((0.2, 0.8), (0.7, 0.8), "road"))
    assert [a.type for a in actions] == [ActionType.SELECT_TOOL, ActionType.DRAG]
    assert actions[1].args == (384, 864, 1344, 864)


def test_zone_rejects_unknown_type():
    mapper = CitiesSkylinesActionMapper(calibration())
    try:
        mapper.zone("office", (0.5, 0.5))
    except ValueError:
        return
    assert False, "Expected ValueError"
