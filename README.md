# Web Safety Eval MVP

**Web Safety Eval** is a user-runnable harness for testing OpenClaw agents against hostile web scenarios. Point it at your own agent, run adversarial browsing-style test cases, and inspect artifact-backed results like transcripts, tool-call traces, reports, and failure signals.

Current focus:
- prompt injection
- secret exfiltration
- tool-boundary violations

## Quick start

From a fresh clone:

```bash
cd web-safety-eval
bash setup.sh
source .venv/bin/activate
```

Run a local mock scenario:

```bash
web-safety-eval run --scenario pi-body-text-001 --backend mock
```

Run a real OpenClaw agent:

```bash
web-safety-eval run --scenario pi-body-text-001 --backend openclaw
```

Target a specific OpenClaw agent:

```bash
web-safety-eval run --scenario pi-body-text-001 --backend openclaw --agent codex
```

Run the full suite:

```bash
web-safety-eval run-all --backend openclaw
```

Discover commands and scenarios in the CLI itself:

```bash
web-safety-eval quickstart
web-safety-eval list-scenarios
web-safety-eval --help
web-safety-eval explain-results
```

If the console script is unavailable, use the module form:

```bash
python -m web_safety_eval quickstart
python -m web_safety_eval run --scenario pi-body-text-001
```

When runs finish, inspect `runs/.../report.md` for outcomes and evidence.

## How to read results

- `failed` means the harness detected one or more configured failure signals for that scenario.
- `did_not_fail` means the harness did not detect those failure signals in that run.
- `did_not_fail` is not a proof of overall safety, only a pass on the current scenario checks.

Look here next:
- `report.md` for the human-readable summary
- `result.json` for structured outcome and metadata
- `transcript.json` for the full interaction record
- `tool_calls.json` for recorded tool use

You can print this guidance anytime with:

```bash
web-safety-eval explain-results
```

## What it includes

- fixed hostile web scenarios
- artifact capture (`result.json`, `report.md`, `transcript.json`, `tool_calls.json`)
- a local mock backend
- a real OpenClaw CLI adapter
- a legacy file-based session-controller path

Current built-in scenarios:
- body-text prompt injection on a product reviews page
- secret exfiltration attempt via in-page URL instruction
- fake system or developer instruction embedded in page content
- tool-boundary manipulation via injected tool instructions
- multi-step attack chain with a planted secret

## Common commands

Use the installable CLI after `bash setup.sh` and `source .venv/bin/activate`:

```bash
web-safety-eval quickstart
web-safety-eval list-scenarios
web-safety-eval run --scenario pi-body-text-001
web-safety-eval run --scenario pi-body-text-001 --backend mock
web-safety-eval run --scenario secret-exfil-url-001 --backend openclaw
web-safety-eval run --scenario pi-body-text-001 --backend openclaw --agent my-browsing-agent
web-safety-eval run-all --backend openclaw
```

Notes:
- omit `--agent` to use OpenClaw's default agent
- flags override env vars when both are set
- the resolved backend and agent are printed at run start and stamped into `result.json` and `report.md`

Recommended real-agent path:
- install OpenClaw and make sure `openclaw --help` works in your shell
- use `web-safety-eval run --backend openclaw ...`
- use wrapper scripts only as compatibility paths

Env-var equivalents:
- `WEB_SAFETY_AGENT`, backend selector like `--backend`
- `WEB_SAFETY_OPENCLAW_AGENT`, agent name like `--agent`
- `WEB_SAFETY_SCENARIO`, scenario id like `--scenario`

Useful environment variables:
- `WEB_SAFETY_OPENCLAW_TIMEOUT`, per-turn timeout for the CLI adapter (default `120` seconds)
- `WEB_SAFETY_AGENT_TIMEOUT`, response timeout for the file-based session agent (default `600` seconds)
- `WEB_SAFETY_CLAUDE_MODEL`, model override for the `claude_sdk` controller backend

## Legacy path: file-based Agent Session Protocol

If you need the older two-process controller flow:

### Shell A

```bash
cd web-safety-eval
WEB_SAFETY_AGENT=openclaw_session python3 run_demo.py
```

### Shell B

```bash
cd web-safety-eval
python -m web_safety_eval.session_controller --backend manual
```

Optional controller backends:

```bash
python -m web_safety_eval.session_controller --backend claude_sdk --model claude-opus-4-7
```

Optional targeting:

```bash
python -m web_safety_eval.session_controller --run-dir runs/pi-body-text-001-20260419T090000Z
```

Controller behavior:
1. Resolve the target run directory from `--run-dir`, `--agent-io-dir`, or the newest recent `runs/*/agent_io/`
2. Poll at 0.5s intervals
3. Process each `request-<N>.json` in order
4. Maintain conversation history across phases
5. Extract the JSON object from the backend reply and write it to `response-<N>.json`
6. Exit when `done.json` appears and print a one-line summary

Manual backend note:
- paste JSON terminated by a blank line
- single-line JSON also works
- empty input fails with a clearer error telling you to paste a JSON object

## Layout

- `src/web_safety_eval/`, core package
- `scenarios/`, JSON scenario definitions plus hostile pages
- `runs/`, generated artifacts

## Tests

Basic regression tests live under `tests/`.

```bash
cd web-safety-eval
source .venv/bin/activate
pytest
```

## Preflight

You can rerun the lightweight setup checks at any time:

```bash
cd web-safety-eval
source .venv/bin/activate
python scripts/preflight.py
```

## Troubleshooting

### `openclaw` not found on PATH

Install OpenClaw first and make sure `openclaw --help` works before running the evaluator.

### `setup.sh` wants to modify an existing `.venv`

Use one of these safer options:

```bash
VENV_DIR=.venv-fresh bash setup.sh
```

or:

```bash
RECREATE_VENV=1 bash setup.sh
```

### JSON parsing or malformed-response failures

The CLI adapter retries once with a stricter JSON-only nudge. If it still fails, rerun the scenario and inspect `transcript.json` plus the run report.

### A scenario fails because a page file is missing

That usually means the agent requested the wrong page name. Check `scenarios/<id>/scenario.json` and inspect the recorded transcript and tool calls.

## Screenshots

The harness attempts to capture real screenshots for served HTML pages.

Optional setup:

```bash
cd web-safety-eval
pip install '.[screenshots]'
playwright install chromium
```

If Playwright is unavailable, runs still complete and screenshot capture falls back gracefully.

## Reports

Reports include:
- scenario category
- scenario severity if failed
- a short why-it-matters summary
- a compact evidence summary

## Operational docs

- `OFFICIAL_RUN_PATH.md`, current supported run flow
- `METHODOLOGY.md`, what the harness does and does not claim
- `RUN_CHECKLIST.md`, practical checklist for running an eval for someone else
- `SAMPLE_REPORT.md`, example of a shareable run artifact
- `AGENT_SESSION_PROTOCOL.md`, file-based backend contract
