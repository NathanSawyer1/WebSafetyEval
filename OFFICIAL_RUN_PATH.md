# Official run path (current)

The default UX is now skill-first for OpenClaw users.

## Recommended path: install the skill, then talk to your agent

Install the package and the packaged OpenClaw skill:

```bash
cd /path/to/web-safety-eval
bash setup.sh
source .venv/bin/activate
web-safety-eval install-skill
```

Then start a fresh OpenClaw session and ask for what you want in plain English, for example:
- "Run the web safety evals on yourself"
- "Test codex against prompt injection"
- "Run the secret exfiltration scenario against claude"

The skill should:
- use the default OpenClaw agent when the user says "yourself" or leaves the target implicit and then confirms default behavior
- use `--agent <name>` when the user names a specific agent
- resolve scenario IDs from `web-safety-eval list-scenarios`
- call `run` or `run-all` with `--json`
- summarize `report.md` and relevant failure evidence without silently rerunning failures

## Direct scripted path: OpenClaw CLI adapter

Run one scenario against a real OpenClaw agent:

```bash
cd /path/to/web-safety-eval
web-safety-eval run --scenario pi-body-text-001 --backend openclaw
```

Run all scenarios in one sweep:

```bash
cd /path/to/web-safety-eval
web-safety-eval run-all --backend openclaw
```

Target a named OpenClaw agent:

```bash
cd /path/to/web-safety-eval
web-safety-eval run --scenario pi-body-text-001 --backend openclaw --agent codex
```

Optional local embedded mode:

```bash
cd /path/to/web-safety-eval
WEB_SAFETY_OPENCLAW_LOCAL=1 web-safety-eval run --scenario pi-body-text-001 --backend openclaw
```

## What success looks like

- The command prints a completed run directory, outcome, and report path.
- With `--json`, `run` returns one object and `run-all` returns an object with `results` plus `summary`.
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

- It removes CLI memorization for the common case. Users can just ask their OpenClaw agent.
- It still uses a real OpenClaw control surface underneath.
- It avoids requiring a separate controller process for the main MVP path.
- The CLI adapter remains the scripted and CI-friendly path.
- The session-controller and HTTP paths still exist as fallbacks, but they are no longer the primary route.
