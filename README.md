# Cities: Skylines Autonomous Agent

Experimental Windows agent for observing and eventually operating Cities: Skylines through screen capture and mouse/keyboard control.

## Phase 10 — verified execution foundation

The project now separates semantic intent from calibrated input and treats execution as a transactional process:

`screen -> perception -> normalized state -> diagnosis/goals -> bounded simulation -> semantic action mapping -> safety policy -> controller -> observe -> verify -> recover/replan`

### Current capabilities

- Screen capture with normalized UI regions
- Structured, confidence-aware `CityState`
- Typed action model with read-only/reversible/destructive safety classes
- Explicit safety policy; autonomous input remains disabled by default
- Goal and hard/soft constraint model
- Deterministic `StrategicManager` and bounded multi-step planner
- Isolated `MockCity` simulation/evaluation with deterministic time progression
- Per-step expected state snapshots
- Resolution-independent camera navigation abstraction
- Semantic camera operations: pan, zoom, rotate, pause and simulation speed
- Calibrated Cities: Skylines action mapping for tools, roads and zoning
- Transactional `PlanExecutor`: dispatch -> observe -> verify -> continue
- Bounded safe retries for failed input dispatch
- Verification confidence thresholding
- Automatic emergency stop on execution or verification failure
- Divergence callback for recovery/replanning integration
- Game sensor/controller adapter protocols
- Recovery state machine and audit history
- Tests for simulation, evaluation, planning, safety, adapters, calibration and execution

### Safety contract

The controller will not send non-read-only input unless the corresponding safety policy is explicitly enabled. Destructive actions require separate explicit permission. A multi-step plan is only an expectation, never permission to blindly continue: every step must be observed and verified before the next step is allowed.

A successful OS-level mouse/keyboard dispatch is **not** considered a successful game action. Verification must come from a meaningful state delta or sufficiently strong visual evidence. Low-confidence effects stop execution instead of allowing the agent to compound uncertainty.

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

Tesseract OCR must also be installed on Windows for OCR.

## Development roadmap

1. ~~Game adapter interfaces~~ **Implemented**
2. ~~Reliable OCR/state extraction foundation~~ **Implemented**
3. ~~Camera/navigation abstraction~~ **Implemented**
4. ~~Mock simulator foundation~~ **Implemented**
5. Semantic verified construction, zoning, utilities and services **In progress**
6. ~~Multi-step planning and replanning~~ **Implemented**
7. Optional LLM/vision planner behind deterministic safety gates
8. Replay/evaluation harness and strategy benchmarking
9. Long-running telemetry, checkpoints and save-game recovery
10. Real-game pilot mode with autonomous input still gated behind explicit policy
