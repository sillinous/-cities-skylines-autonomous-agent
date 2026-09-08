# Cities: Skylines Autonomous Agent

Experimental Windows agent for observing and eventually operating Cities: Skylines through screen capture and mouse/keyboard control.

## Phase 12 — vision intent and deterministic safety gates

The project now has an explicit boundary between visual/model interpretation and game control:

`screen -> perception/OCR/vision -> normalized state + semantic intents -> deterministic validation -> simulation/strategy -> safety policy -> calibrated controller -> observe -> semantic verify -> recover/replan`

### Current capabilities

- Screen capture with normalized UI regions
- Structured, confidence-aware `CityState`, including service coverage and budget telemetry
- Injectable vision backend with a safe no-op default
- Semantic `Intent` model for observation, construction, zoning, utilities, services, bulldozing and budgets
- Confidence validation before an intent can reach execution
- Deterministic `VisionIntentPlanner` that converts intents into typed actions
- Safety policy remains the final authorization boundary; the vision layer cannot dispatch input
- Explicit read-only/reversible/destructive safety classes
- Deterministic strategic manager and bounded multi-step planner
- Isolated `MockCity` simulation/evaluation with deterministic time progression
- Semantic construction and calibrated action mapping
- Transactional plan executor with verification, retries and emergency stop
- Recovery state machine, audit history and GitHub Actions CI

### Safety contract

The controller will not send non-read-only input unless the corresponding safety policy is explicitly enabled. Destructive actions require separate explicit permission. Model-generated or vision-generated intents are **never** trusted as execution authority.

A successful OS-level mouse/keyboard dispatch is not considered a successful game action. Semantic state deltas are preferred. Generic screen changes are low-confidence evidence and cannot satisfy the default verification threshold.

If perception is uncertain, the agent observes or recovers rather than guessing. Calibration is explicit; UI coordinates are never inferred from a model and blindly executed.

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
7. ~~Vision intent layer behind deterministic safety gates~~ **Implemented**
8. Replay/evaluation harness and strategy benchmarking **Next**
9. Long-running telemetry, checkpoints and save-game recovery
10. Real-game pilot mode with autonomous input still gated behind explicit policy
