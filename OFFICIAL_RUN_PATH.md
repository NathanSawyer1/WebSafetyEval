# Official run path (current)

This is the simplest supported run flow today.

## Primary path: OpenClaw skill

After installing the harness, install the skill once:

```bash
cd /path/to/web-safety-eval
bash setup.sh
source .venv/bin/activate
web-safety-eval install-skill
```

Then just talk to your OpenClaw agent:

- "run the web safety evals on yourself"
- "test codex against prompt injection"
- "run all scenarios against claude"

The skill runs the CLI under the hood, summarizes `report.md`, and points you at
the run artifacts.

## Scripted path: CLI

For CI and scripting, run the CLI directly.

Run one scenario against a real OpenClaw agent:

```bash
cd /path/to/web-safety-eval
WEB_SAFETY_SCENARIO=pi-body-text-001 WEB_SAFETY_AGENT=openclaw python3 run_demo.py
```

Or the installable CLI with `--json` for machine-parseable output:

```bash
web-safety-eval run --scenario pi-body-text-001 --backend openclaw --json
web-safety-eval run-all --backend openclaw --json
```

Replace `WEB_SAFETY_SCENARIO` as needed.

To run all scenarios in one sweep (env-var form):

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

- The skill surface means users don't have to memorize CLI flags — they just ask their OpenClaw agent.
- Under the hood the skill uses the real OpenClaw CLI adapter that users can run today.
- The CLI and env-var paths stay available for scripting and CI.
- The session-controller and HTTP paths still exist as fallbacks, but they are no longer the primary route.
