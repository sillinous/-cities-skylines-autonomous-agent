# Cities: Skylines Autonomous Agent

Experimental Windows agent for observing and eventually operating Cities: Skylines through screen capture and mouse/keyboard control.

## Phase 4 — architecture foundation

The project now has a game-version-neutral control architecture:

`screen -> perception -> normalized state -> goals -> strategy -> typed actions -> safety policy -> controller -> verification/recovery -> audit`

The normalized state and action layers are intentionally independent of exact UI coordinates, so Cities: Skylines and Cities: Skylines II can later use separate adapters without rewriting the strategic core.

### Current capabilities

- Screen capture with normalized UI regions
- Structured, confidence-aware `CityState`
- Typed action model with read-only/reversible/destructive safety classes
- Explicit safety policy; autonomous input remains disabled by default
- Goal and hard/soft constraint model
- Deterministic baseline strategy that refuses to guess when evidence is insufficient
- Recovery state machine for verification failures
- In-memory audit event history
- Unit tests for state, OCR, planner, safety, goals, and recovery

### Safety contract

The controller will not send non-read-only input unless the corresponding safety policy is explicitly enabled. Destructive actions require a separate explicit permission. This is deliberate: reliable perception and verification must exist before autonomous city-changing behavior is enabled.

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
4. Mock simulator for planning tests without the game
5. Verified construction, zoning, utilities and services
6. Closed-loop strategic city manager
7. Optional LLM planner behind deterministic safety gates
8. Replay/evaluation harness
9. Long-running telemetry, checkpoints and save-game recovery
