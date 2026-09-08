# Cities: Skylines Autonomous Agent

Experimental Windows agent for observing and eventually operating Cities: Skylines through screen capture and mouse/keyboard control.

## Phase 7 — game adapter and calibration foundation

The project now has a game-version-neutral control architecture:

`screen -> perception -> normalized state -> diagnosis/goals -> bounded simulation -> safety policy -> controller -> verification/recovery -> audit -> replan`

The strategic core is deliberately separated from game-specific UI details. Concrete Cities: Skylines and Cities: Skylines II adapters can implement the same sensor/controller interfaces while using different UI maps.

### Current capabilities

- Screen capture with normalized UI regions
- Structured, confidence-aware `CityState`
- Typed action model with read-only/reversible/destructive safety classes
- Explicit safety policy; autonomous input remains disabled by default
- Goal and hard/soft constraint model
- Deterministic `StrategicManager` and bounded multi-step planner
- Isolated `MockCity` simulation/evaluation with deterministic time progression
- Per-step expected state snapshots, verification and plan invalidation
- Explicit replanning after state divergence
- Game sensor/controller adapter protocols
- Cities: Skylines adapter composition point
- Resolution-independent normalized UI calibration primitives
- Recovery state machine and audit history
- Tests for simulation, evaluation, planning, safety, adapters and calibration

### Safety contract

The controller will not send non-read-only input unless the corresponding safety policy is explicitly enabled. Destructive actions require separate explicit permission. A multi-step plan is only an expectation, never permission to blindly continue: every step must be verified against observed state before the next step is allowed.

The adapter layer does not guess UI coordinates. Calibration must be explicit, and uncertain perception should leave the strategic layer in observation/recovery mode.

## Windows setup

Python 3.11+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
py -m cities_agent
```

Tesseract OCR must also be installed on Windows for OCR. Put it on PATH; game-specific OCR mappings will be added with the Cities: Skylines UI adapter.

## Development roadmap

1. ~~Game-specific UI adapters for Cities: Skylines / Cities: Skylines II~~ **Adapter interfaces implemented**
2. Reliable OCR and visual detection with confidence scoring
3. Camera/navigation abstraction
4. ~~Expand the mock simulator with roads, utilities and services~~ **Implemented foundation**
5. Verified construction, zoning, utilities and services
6. ~~Multi-step planning and replanning~~ **Implemented**
7. Optional LLM/vision planner behind deterministic safety gates
8. Replay/evaluation harness and strategy benchmarking
9. Long-running telemetry, checkpoints and save-game recovery
10. Real-game pilot mode with autonomous input still gated behind explicit policy
