from cities_agent.planner import SafeStarterPlanner
from cities_agent.perception import Observation
from PIL import Image

def test_starter_planner_is_safe():
    obs = Observation(Image.new("RGB", (10, 10)), 10, 10)
    assert SafeStarterPlanner().plan(obs).actions == []
