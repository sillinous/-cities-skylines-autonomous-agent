from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from .actions import Action, ActionType, SafetyClass
from .simulator import MockCity, SimConfig
from .state import CityState

def action_to_dict(a: Action) -> dict:
    return {"type": a.type.value, "args": list(a.args), "safety": a.safety.value, "expected_effect": a.expected_effect,
            "preconditions": list(a.preconditions), "max_retries": a.max_retries, "timeout_seconds": a.timeout_seconds}

def action_from_dict(d: dict) -> Action:
    return Action(ActionType(d["type"]), tuple(d.get("args", [])), SafetyClass(d.get("safety", "read_only")),
                  d.get("expected_effect", ""), tuple(d.get("preconditions", [])), int(d.get("max_retries", 0)), float(d.get("timeout_seconds", 3.0)))

def state_from_dict(d: dict | None) -> CityState | None:
    if d is None: return None
    d = dict(d); d["warnings"] = tuple(d.get("warnings", ()))
    d["service_coverage"] = dict(d.get("service_coverage", {})); d["budgets"] = dict(d.get("budgets", {})); d["confidence"] = dict(d.get("confidence", {}))
    return CityState(**d)

@dataclass(frozen=True)
class ReplayEvent:
    index: int
    action: Action
    before: CityState | None = None
    after: CityState | None = None
    executed: bool = False
    verified: bool = False
    verification_confidence: float = 0.0
    reason: str = ""
    def to_dict(self) -> dict:
        return {"index": self.index, "action": action_to_dict(self.action), "before": self.before.to_dict() if self.before else None,
                "after": self.after.to_dict() if self.after else None, "executed": self.executed, "verified": self.verified,
                "verification_confidence": self.verification_confidence, "reason": self.reason}
    @classmethod
    def from_dict(cls, d: dict) -> "ReplayEvent":
        return cls(int(d["index"]), action_from_dict(d["action"]), state_from_dict(d.get("before")), state_from_dict(d.get("after")),
                   bool(d.get("executed")), bool(d.get("verified")), float(d.get("verification_confidence", 0.0)), d.get("reason", ""))

@dataclass
class ReplayEpisode:
    episode_id: str
    seed: int = 0
    events: list[ReplayEvent] = field(default_factory=list)
    def record(self, event: ReplayEvent) -> None:
        if event.index != len(self.events): raise ValueError("Replay indexes must be contiguous and zero-based.")
        self.events.append(event)
    @property
    def actions(self) -> tuple[Action, ...]: return tuple(e.action for e in self.events if e.executed)
    @property
    def safety_stops(self) -> int: return sum(e.executed and not e.verified for e in self.events)
    @property
    def verification_failures(self) -> int: return sum(not e.verified for e in self.events if e.executed)
    def to_jsonl(self) -> str:
        header = json.dumps({"kind":"replay_episode", "episode_id":self.episode_id, "seed":self.seed}, sort_keys=True)
        return "\n".join([header] + [json.dumps(e.to_dict(), sort_keys=True) for e in self.events]) + "\n"
    @classmethod
    def from_jsonl(cls, text: str) -> "ReplayEpisode":
        lines = [x for x in text.splitlines() if x.strip()]
        if not lines: raise ValueError("Replay is empty.")
        h = json.loads(lines[0])
        if h.get("kind") != "replay_episode": raise ValueError("Invalid replay header.")
        out = cls(str(h["episode_id"]), int(h.get("seed", 0)))
        for line in lines[1:]: out.record(ReplayEvent.from_dict(json.loads(line)))
        return out
    def save(self, path: str | Path) -> None: Path(path).write_text(self.to_jsonl(), encoding="utf-8")
    @classmethod
    def load(cls, path: str | Path) -> "ReplayEpisode": return cls.from_jsonl(Path(path).read_text(encoding="utf-8"))
    def replay(self, config: SimConfig | None = None) -> tuple[CityState, tuple[bool, ...]]:
        city = MockCity(config or SimConfig(starting_money=50_000 + self.seed)); accepted = []
        for action in self.actions: accepted.append(city.apply(action)); city.wait(1)
        return city.state, tuple(accepted)

@dataclass(frozen=True)
class ReplayMetrics:
    episode_id: str; action_count: int; accepted_count: int; verified_count: int
    verification_failures: int; safety_stops: int; score: float
    money_delta: int | None; population_delta: int | None

def measure_replay(episode: ReplayEpisode, config: SimConfig | None = None) -> ReplayMetrics:
    final, accepted = episode.replay(config); before = next((e.before for e in episode.events if e.before), None)
    from .evaluator import SimulationEvaluator
    score = SimulationEvaluator.score(before, final) if before else 0.0
    md = None if not before or before.money is None or final.money is None else final.money - before.money
    pd = None if not before or before.population is None or final.population is None else final.population - before.population
    return ReplayMetrics(episode.episode_id, len(episode.actions), sum(accepted), sum(e.verified for e in episode.events), episode.verification_failures, episode.safety_stops, score, md, pd)
