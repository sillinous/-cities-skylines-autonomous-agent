from __future__ import annotations

import time

from .config import Config
from .control import SafetyController
from .ocr import OcrEngine
from .perception import ScreenObserver
from .planner import SafeStarterPlanner
from .state import CityState
from .state_parser import StateParser


class Agent:
    def __init__(self, config: Config):
        self.config = config
        self.observer = ScreenObserver()
        self.controller = SafetyController(allow_input=config.enabled)
        self.parser = StateParser(OcrEngine())
        self.planner = SafeStarterPlanner()
        self.state = CityState()

    def run_once(self):
        observation = self.observer.capture()
        self.state = self.parser.parse(observation)
        plan = self.planner.plan(observation, self.state)
        results = [
            self.controller.execute(a)
            for a in plan.actions[: self.config.max_actions_per_cycle]
        ]
        return observation, plan, results

    def run(self):
        while not self.controller.stopped:
            self.run_once()
            time.sleep(self.config.loop_seconds)
