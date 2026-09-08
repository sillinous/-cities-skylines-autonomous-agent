# Cities: Skylines Autonomous Agent

Experimental Windows agent for observing and eventually operating Cities: Skylines through screen capture and mouse/keyboard control.

## Phase 6 — bounded planning and replanning

The project now has a game-version-neutral control architecture:

`screen -> perception -> normalized state -> diagnosis/goals -> candidate actions -> bounded simulation -> safety policy -> controller -> verification/recovery -> audit -> replan`

The normalized state and action layers are independent of exact UI coordinates, so Cities: Skylines and Cities: Skylines II can later use separate adapters without rewriting the strategic core.

### Current capabilities

- Screen capture with normalized UI regions
- Structured, confidence-aware `CityState`
- Typed action model with read-only/reversible/destructive safety classes
- Explicit safety policy; autonomous input remains disabled by default
- Goal and hard/soft constraint model
- Deterministic `StrategicManager` that diagnoses state and ranks objectives
- Candidate generation and isolated `MockCity` simulation/evaluation
- Bounded multi-step look-ahead planning
- Per-step expected state snapshots for verification
- Plan invalidation and explicit replanning when observed state diverges
- Deterministic time/wait simulation for closed-loop planning
- Known utility failures can be planned as repair actions; uncertainty/warnings remain hard stops
- Hard safety conditions force observation-only behavior
- Recovery state machine for verification failures
- In-memory audit event history
- Unit tests for state, OCR, planner, safety, goals/recovery, simulation, evaluation and replanning

### Safety contract

The controller will not send non-read-only input unless the corresponding safety policy is explicitly enabled. Destructive actions require separate explicit permission. The strategic manager also refuses to act when a hard safety condition is active or when no candidate has positive simulated value.

A multi-step plan is only an expectation, never permission to blindly continue. Each step has an expected state; divergence invalidates the remaining plan and triggers replanning. This is deliberate: reliable perception, simulation, execution gating and verification must exist before autonomous city-changing behavior is enabled.

## Windows setup

Python 3.11+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
py -m cities_agent
```

Tesseract OCR must also be installed on Windows for OCR. Put it on PATH; explicit executable configuration will be added with the UI adapter layer.

## Development roadmap

1. Game-specific UI adapters for Cities: Skylines / Cities: Skylines II
2. Reliable OCR and visual detection with confidence scoring
3. Camera/navigation abstraction
4. Expand the mock simulator with roads, utilities and services
5. Verified construction, zoning, utilities and services
6. ~~Multi-step planning and replanning~~ **Implemented**
7. Optional LLM/vision planner behind deterministic safety gates
8. Replay/evaluation harness and strategy benchmarking
9. Long-running telemetry, checkpoints and save-game recovery
10. Real-game pilot mode with autonomous input still gated behind explicit policy
