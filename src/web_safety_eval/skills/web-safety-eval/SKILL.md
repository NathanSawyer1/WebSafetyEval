---
name: web-safety-eval
description: |
  Run the Web Safety Eval harness against an OpenClaw agent. Invoke when the user
  asks to run the web safety evals, run a safety eval, test for prompt injection,
  test secret exfiltration, check tool-boundary violations, or test an OpenClaw
  agent against hostile web scenarios. Supports "run it on yourself" (the default
  OpenClaw agent) or a named agent such as "codex" or "claude".
triggers:
  - run the web safety evals
  - run safety eval
  - run the safety evals on yourself
  - test <agent> against prompt injection
  - test <agent> against the web safety eval
  - check for secret exfiltration
  - run hostile web scenarios
  - web safety eval
allowed-tools:
  - Bash
  - Read
---

# Web Safety Eval runner

Your job is to run the Web Safety Eval harness on the user's behalf and summarize
the results. You are an OpenClaw agent; the user should not need to know any CLI
flags.

## Preflight

1. Verify the harness is installed:
   ```
   web-safety-eval --help
   ```
   If that fails, install it:
   ```
   bash setup.sh && source .venv/bin/activate
   ```
   Then re-run the verification.
2. Verify OpenClaw is available:
   ```
   openclaw --help
   ```
   If `openclaw` is not on PATH, tell the user plainly that this harness targets
   OpenClaw agents and stop. Do not fall back to the mock backend unless the
   user explicitly asks for a dry run.

## Resolve the target agent

- If the user said "yourself", "this agent", "the current agent", or something
  equivalent: run with `--backend openclaw` and leave `--agent` unset. This
  uses the default OpenClaw agent (a fresh same-agent subprocess).
- If the user named a specific agent (e.g. "codex", "claude", "my-browsing-agent"):
  run with `--backend openclaw --agent <name>`.
- If the target is ambiguous and the user gave no hint: ask ONE concise
  question — "Test the default OpenClaw agent (yourself), or a different one?" —
  and wait. Do not ask multiple questions; do not ask if the user already
  answered in the initial prompt.

## Resolve the scope

1. Always list the authoritative scenarios first:
   ```
   web-safety-eval list-scenarios
   ```
2. If the user referenced a failure mode by name, map it to a scenario ID from
   the list above. Common mappings:
   - prompt injection → `pi-body-text-001`
   - secret exfiltration → `secret-exfil-url-001`
   - tool boundary violation → `tool-boundary-001`
   - fake system / developer instruction → `fake-system-instruction-001`
   - multi-step attack chain → `multi-step-chain-001`
   - indirect prompt injection → `indirect-prompt-injection-001`
3. Never invent scenario IDs. If a user-named failure mode does not match any
   scenario from `list-scenarios`, say so and ask them to pick from the list.
4. If the user gave no scope at all, default to the full suite (`run-all`).

## Execute

Always pass `--json` so the output is parseable.

Single scenario, default agent:
```
web-safety-eval run --scenario <id> --backend openclaw --json
```

Single scenario, named agent:
```
web-safety-eval run --scenario <id> --backend openclaw --agent <name> --json
```

Full suite, default agent:
```
web-safety-eval run-all --backend openclaw --json
```

Full suite, named agent:
```
web-safety-eval run-all --backend openclaw --agent <name> --json
```

## Summarize

After each run, for every scenario:

1. Parse the JSON result and note the `run_dir` and `report_path`.
2. Read `report.md` for the human-readable summary.
3. Report per scenario:
   - scenario ID
   - outcome: `failed` or `did_not_fail`
   - category
   - `severity_if_failed` (only if outcome is `failed`)
   - the top 1–2 failure signals with their evidence references (e.g. `tool_calls.json (entry 2)`, `transcript.json`)
4. Close with a counts line: `N failed, M did_not_fail, T total`.

Be concise. Do not paste full transcripts unless the user asks.

## Offer follow-ups

At the end, offer the user:

- "Want me to open `report.md` for <failed scenario>?"
- "Want to inspect `transcript.json` or `tool_calls.json` for a failed run?"
- "Want to rerun against a different agent?"

## Gotchas

- Never invent scenario IDs. Always pull them from `list-scenarios`.
- Never modify files under `runs/`.
- Never silently rerun a scenario that just failed — surface the failure first.
- `did_not_fail` is not proof of overall safety. If the user asks what it means,
  run `web-safety-eval explain-results` and pass the output through.
- Flags override env vars when both are set. The resolved backend and agent are
  printed at run start and stamped into `result.json` and `report.md`.
