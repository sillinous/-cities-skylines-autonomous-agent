from .agent import Agent
from .config import Config

if __name__ == "__main__":
    config = Config()
    print("Cities: Skylines Autonomous Agent")
    print("Input enabled:", config.enabled)
    Agent(config).run()
