# Design-Partner Eval Run Checklist

Use this checklist when running an evaluation for another person or team.

## Before the run

- Confirm which scenario or scenario set you want to run.
- Confirm whether you are using:
  - mock path
  - session-driven path
- If using session-driven path, use the official flow in `OFFICIAL_RUN_PATH.md`.
- Confirm the environment is inside `web-safety-eval/` with `PYTHONPATH=src`.
- If screenshots are expected, confirm Playwright/Chromium is installed.

## During the run

- Start the harness.
- Start the controller if needed.
- Confirm a fresh run directory appears under `runs/`.
- Confirm `agent_io/` request and response files are being created for session-driven runs.
- Watch for empty-input or malformed JSON controller errors and correct them immediately.

## After the run

Check that the run directory contains:
- `result.json`
- `report.md`
- `tool_calls.json`
- `transcript.json`
- `pages/`
- `agent_io/` for session-driven runs
- `screens/` if screenshot capture succeeded

## Review the result

- Check the outcome.
- Read the findings.
- Inspect the evidence summary.
- Read the final answer.
- Confirm the result matches the observed run behavior.

## Communicate carefully

When sharing results:
- say what scenario was tested
- say whether the run failed or did not fail
- include the caveat that this is not a safety certification
- avoid implying broad security guarantees

## If something goes wrong

- If the controller fails, restart from the official run path.
- If a session-driven run times out, check which response file was missing.
- If screenshot capture is missing, confirm whether Playwright is installed.
- If a result looks suspicious, inspect `transcript.json` and `tool_calls.json` first.

## Minimum success bar for a useful run

A run is useful if it produces:
- a complete run directory
- a coherent report
- enough evidence to explain the outcome
- at least one actionable takeaway or clear validation result
