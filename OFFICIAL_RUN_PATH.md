# Official run path (current)

This is the simplest supported run flow today.

## Recommended path: OpenClaw CLI adapter

Run one scenario against a real OpenClaw agent:

```bash
cd /path/to/web-safety-eval
WEB_SAFETY_SCENARIO=pi-body-text-001 WEB_SAFETY_AGENT=openclaw python3 run_demo.py
```

Replace `WEB_SAFETY_SCENARIO` as needed.

To run all scenarios in one sweep:

```bash
cd /path/to/web-safety-eval
WEB_SAFETY_AGENT=openclaw python3 run_all.py
```

Optional local embedded mode:

```bash
cd /path/to/web-safety-eval
WEB_SAFETY_AGENT=openclaw WEB_SAFETY_OPENCLAW_LOCAL=1 python3 run_demo.py
```

## What success looks like

- The command prints a completed run directory, outcome, and report path.
- The run directory contains:
  - `result.json`
  - `report.md`
  - `tool_calls.json`
  - `transcript.json`
  - screenshot artifacts when available

## Fallback path: file-based session controller

If you need the older two-process path:

### Shell A

```bash
cd /path/to/web-safety-eval
WEB_SAFETY_SCENARIO=pi-body-text-001 WEB_SAFETY_AGENT=openclaw_session python3 run_demo.py
```

### Shell B

```bash
cd /path/to/web-safety-eval
PYTHONPATH=src python3 -m web_safety_eval.session_controller --backend manual
```

Optional backends:

```bash
PYTHONPATH=src python3 -m web_safety_eval.session_controller --backend claude_sdk --model claude-opus-4-7
```

```bash
OPENCLAW_HTTP_URL=http://127.0.0.1:8765 PYTHONPATH=src python3 -m web_safety_eval.session_controller --backend openclaw_http
```

## Why this is the official path now

- It uses a real OpenClaw control surface that users can run today.
- It avoids requiring a separate controller process for the main MVP path.
- It has already been exercised across multiple real scenarios.
- The session-controller and HTTP paths still exist as fallbacks, but they are no longer the primary route.
