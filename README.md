# Cities: Skylines Autonomous Agent

Experimental Windows agent for observing and eventually operating Cities: Skylines through screen capture and mouse/keyboard control.

## Phase 11 — semantic construction layer

The execution stack now distinguishes **semantic construction intent** from the calibrated mouse/keyboard events needed to perform it:

`screen -> perception -> normalized state -> diagnosis/goals -> simulation -> semantic construction -> calibrated mapping -> safety policy -> controller -> observe -> semantic verify -> recover/replan`

### Current capabilities

- Screen capture with normalized UI regions
- Structured, confidence-aware `CityState`, including service coverage and budget telemetry
- Typed action model with read-only/reversible/destructive safety classes
- Explicit safety policy; autonomous input remains disabled by default
- Goal and hard/soft constraint model
- Deterministic `StrategicManager` and bounded multi-step planner
- Isolated `MockCity` simulation/evaluation with deterministic time progression
- Simulator modeling for roads, zoning, utilities, services, budgets and bulldozing
- Semantic `ConstructionActions` for road, zoning, utility, service, bulldoze and budget intent
- Calibration-driven mapping of semantic construction into low-level tool selection, clicks and drags
- Transactional `PlanExecutor`: dispatch -> observe -> verify -> continue
- Verification based on meaningful state deltas for supported construction effects
- Safe retries and automatic emergency stop on execution/verification failure
- Divergence callback for recovery/replanning integration
- Game sensor/controller adapter protocols
- Recovery state machine and audit history
- GitHub Actions CI for Python 3.11 and 3.12

### Safety contract

The controller will not send non-read-only input unless the corresponding safety policy is explicitly enabled. Destructive actions require separate explicit permission. A multi-step plan is only an expectation, never permission to blindly continue: every step must be observed and verified before the next step is allowed.

A successful OS-level mouse/keyboard dispatch is **not** considered a successful game action. Semantic state deltas are preferred. Generic screen changes are treated as low-confidence evidence and cannot satisfy the default 0.80 verification threshold.

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
5. ~~Semantic construction layer~~ **Implemented**
6. ~~Multi-step planning and replanning~~ **Implemented**
7. Optional LLM/vision planner behind deterministic safety gates **Next**
8. Replay/evaluation harness and strategy benchmarking
9. Long-running telemetry, checkpoints and save-game recovery
10. Real-game pilot mode with autonomous input still gated behind explicit policy
