# Web Safety Eval Methodology

## Purpose

Web Safety Eval is a controlled evaluation harness for testing whether a browsing-capable agent exhibits dangerous behavior when interacting with hostile web content.

It is designed to surface evidence of specific failure modes under adversarial conditions.

## What this project is

This project is:
- a hostile-web evaluation harness
- a controlled scenario runner
- an artifact and report generator
- a tool for identifying concrete failure modes

## What this project is not

This project is not:
- a certification system
- proof that an agent is safe
- a comprehensive security evaluation
- a guarantee of production readiness
- a substitute for broader security review

## Current evaluation categories

The current MVP scenarios cover:
- prompt injection
- secret exfiltration
- instruction hierarchy violations
- tool-boundary manipulation
- multi-step attack chains

## Evaluation model

Each run executes a specific scenario in a controlled environment.

The harness captures:
- transcript
- tool calls
- served HTML
- screenshots when available
- result summary
- markdown report

Each scenario defines:
- a task
- hostile or deceptive page content
- expected safe behavior
- failure conditions
- severity if failed

## Outcome interpretation

Possible outcomes include:
- `failed` — the run matched one or more defined failure conditions
- `did_not_fail` — the run did not match the defined failure conditions in that scenario

A `did_not_fail` result does not mean the agent is safe. It only means the targeted failure mode did not appear in that specific controlled run.

## How to read the reports

Reports are intended to answer:
- what scenario was tested
- what happened
- what evidence was captured
- why the result matters

The most important fields are:
- outcome
- category
- severity if failed
- findings
- evidence summary
- final answer

## Key limitations

Current limitations include:
- limited scenario coverage
- manual-controller workflow for the official session-driven run path
- optional rather than guaranteed screenshot capture
- no claim of real-internet fidelity
- no guarantee that passing behavior generalizes across models, prompts, or future versions

## Recommended use

Use this harness to:
- identify concrete browsing-related failure modes
- compare behavior across scenarios
- generate artifacts for review
- guide mitigation work

Do not use this harness to:
- market an agent as certified safe
- claim broad security guarantees
- replace ongoing evaluation as models and prompts change

## Backend model

The harness uses the Agent Session Protocol as its agent integration boundary.
Current backends include:
- `manual` for dev/debug use
- `claude_sdk` as the current reference automated backend

Additional backends can be added without changing the scenario harness itself.

## Current maturity

This is an MVP-stage evaluation harness. It is appropriate for internal use, exploratory red-teaming, and early design-partner feedback.
