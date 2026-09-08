# Cities: Skylines Autonomous Agent

Experimental Windows agent for observing and eventually operating Cities: Skylines through screen capture and mouse/keyboard control.

## Phase 16 — Windows integration bridge

The project now has the first platform bridge needed for a controlled live-game pilot:

`screen -> perception/OCR/vision -> normalized state + semantic intents -> deterministic validation -> simulation/strategy -> safety policy -> pilot preflight -> calibrated semantic compiler -> Windows game-window checks -> calibrated controller -> observe -> semantic verify -> recover/replan -> replay/evaluate/benchmark -> telemetry/checkpoint`

### Current capabilities

- Screen capture with normalized UI regions
- Structured, confidence-aware `CityState`, including service coverage and budget telemetry
- Injectable vision backend with a safe no-op default
- Semantic `Intent` model for observation, construction, zoning, utilities, services, bulldozing and budgets
- Confidence validation before an intent can reach execution
- Deterministic `VisionIntentPlanner` that converts intents into typed actions
- `IntentCompiler` translating validated semantic intents into calibrated low-level actions without dispatching OS input
- Safety policy remains the final authorization boundary; the vision layer cannot dispatch input
- Explicit read-only/reversible/destructive safety classes
- Deterministic strategic manager and bounded multi-step planner
- Isolated `MockCity` simulation/evaluation with deterministic time progression
- Semantic construction and calibrated action mapping
- Transactional plan executor with verification, retries and emergency stop
- Recovery state machine, audit history and GitHub Actions CI
- Append-only JSONL replay episodes that preserve actions, states and verification outcomes
- Deterministic replay of recorded action sequences against the simulator
- Replay metrics for score, acceptance, verification failures, safety stops, money and population deltas
- Strategy benchmark runner for comparing strategies across deterministic seeds
- Append-only operational telemetry with sequence validation and optional JSONL persistence
- Restart-safe versioned checkpoints containing logical state, pending actions and planner context
- Atomic checkpoint replacement and explicit checkpoint clearing
- Controlled real-game pilot guard with game-detection, foreground, calibration and pause preflight gates
- Dry-run controller that records intended actions without dispatching mouse/keyboard input
- Per-cycle pilot action budget and hard halt state
- Windows game-window adapter for case-insensitive Cities: Skylines title detection, foreground validation and window resolution discovery
- Resolution-bound calibration profiles that reject mismatched observations

### Safety contract

The controller will not send non-read-only input unless the corresponding safety policy is explicitly enabled. Destructive actions require separate explicit permission. Model-generated or vision-generated intents are **never** trusted as execution authority.

The pilot layer adds independent preflight gates: the game must be detected, be the foreground application, have resolution-matched calibration, and normally be paused before input. Dry-run mode is the default and intentionally blocks real input.

A successful OS-level mouse/keyboard dispatch is not considered a successful game action. Semantic state deltas are preferred. Generic screen changes are low-confidence evidence and cannot satisfy the default verification threshold.

If perception is uncertain, the agent observes or recovers rather than guessing. Calibration is explicit; UI coordinates are never inferred from a model and blindly executed.

Replay, benchmarking, telemetry and checkpoint persistence do not grant or bypass real-game input authority. A checkpoint is a logical recovery record; it does **not** load, overwrite, or restore a Cities: Skylines save file.

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
8. ~~Replay/evaluation harness and strategy benchmarking~~ **Implemented**
9. ~~Long-running telemetry and restart-safe checkpoints~~ **Implemented**
10. ~~Controlled real-game pilot infrastructure~~ **Implemented**
11. Real save-game integration only after a separate backup/restore safety boundary is designed and tested
12. ~~Calibrated semantic-to-input compiler~~ **Implemented**
13. Real-game state verification and live agent-loop integration
