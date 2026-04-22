---
name: web-safety-eval
description: Run web safety evaluation scenarios against OpenClaw agents from plain-English user requests.
keywords:
  - web safety eval
  - prompt injection
  - secret exfiltration
  - tool boundary
  - indirect prompt injection
  - test codex
  - test claude
  - run evals on yourself
---

# Web Safety Eval skill

Use this skill when a user wants to run the `web-safety-eval` package from natural language instead of memorizing the CLI.

## Goal

Turn requests like these into the right evaluation and a useful summary:
- "run the web safety evals on yourself"
- "test codex against prompt injection"
- "run the secret exfiltration scenario against claude"

## How it works

This skill spawns an isolated subagent to run the eval. The subagent has its own exec permissions, so the user only needs to approve the spawn, not every command.

## Preflight

1. Confirm the repo is at `/home/nathan/repos/web-safety-eval`.
2. Confirm `openclaw agents list` works.
3. If OpenClaw is unavailable, stop and tell the user this harness only supports OpenClaw for agent-native runs.

## Resolve the target agent

- If the user says "yourself" or clearly means the default OpenClaw agent, use the default (omit agent name).
- If the user names an agent, first get the list of available agents via `openclaw agents list --json`.
- Validate the named agent is in the list. If not, tell the user which agents are available.
- If the user does not indicate a target at all, ask once: `Test the default OpenClaw agent (yourself), or a different one?`
- Do not ask again after the user answers.

## Resolve the scope

- Never invent scenario IDs.
- Use these convenience mappings when they match the user's wording:
  - prompt injection -> `pi-body-text-001`
  - secret exfiltration -> `secret-exfil-url-001`
  - tool boundary -> `tool-boundary-001`
  - fake system instruction -> `fake-system-instruction-001`
  - multi-step chain -> `multi-step-chain-001`
  - indirect prompt injection -> `indirect-prompt-injection-001`
- If the user gives no clear failure-mode hint, default to running all scenarios.

## Execute

### Option A: Spawn an isolated eval runner

Use `sessions_spawn` to create an ephemeral subagent that runs the eval:

```
Task for spawned subagent:
Run the following web-safety-eval commands in /home/nathan/repos/web-safety-eval:

1. First, activate the venv: source .venv/bin/activate
2. List available scenarios: python -m web_safety_eval list-scenarios
3. Run the eval:
   - For a single scenario: python -m web_safety_eval run --scenario <scenario_id> --backend openclaw --json
   - For all scenarios: python -m web_safety_eval run-all --backend openclaw --json
4. Return the results in this format:
   - For single: {outcome, scenario_id, failures: [], report_path}
   - For run-all: {results: [...], summary: {total, failed, did_not_fail}}
```

### Option B: Direct CLI (if exec is already allowed)

If the agent already has exec permissions for the venv python, run directly:

```bash
cd /home/nathan/repos/web-safety-eval
source .venv/bin/activate
python -m web_safety_eval run --scenario <scenario_id> --backend openclaw --json
```

## Summarize results

Parse the JSON output and summarize:
- outcome
- category
- severity if failed
- the top one or two failure signals with evidence references when present

Close with a counts line.

## Good follow-ups to offer

- open `report.md`
- inspect `transcript.json` for a failed run
- rerun against a different named OpenClaw agent