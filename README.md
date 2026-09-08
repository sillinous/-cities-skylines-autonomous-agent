# Cities: Skylines Autonomous Agent

An experimental Windows agent for observing and operating Cities: Skylines through screen capture and mouse/keyboard control.

## Status
Phase 1 foundation. The default runtime is DRY-RUN / SAFE: it observes and plans but does not send input unless explicitly enabled.

## Architecture
Screen capture -> perception -> state model -> planner -> action controller -> verification -> repeat.

## Safety
- Autonomous input is disabled by default.
- Destructive actions are blocked by policy in the initial foundation.
- Use a disposable/test save while developing.

## Quick start
Windows + Python 3.11+:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py -m cities_agent
```

Set AGENT_ENABLE_INPUT=1 only after the dry-run path is verified.

## Roadmap
1. Reliable window capture
2. UI/OCR perception
3. Game-state model
4. Action verification
5. Camera navigation
6. Strategic city manager
7. Optional LLM planning
8. Replay/evaluation harness
