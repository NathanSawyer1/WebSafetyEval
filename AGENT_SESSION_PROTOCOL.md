# Agent Session Protocol v0

## Purpose

The Agent Session Protocol defines the boundary between the Python evaluation harness and any agent backend that can make decisions during a run.

This protocol is the product-facing integration surface for the MVP.

## Design goals

- backend-agnostic
- file-based and simple to debug
- deterministic artifact layout
- easy to service manually or programmatically
- suitable for multiple adapters

## Core idea

The evaluation harness writes request files into a run directory.
A controller or backend reads those requests, produces JSON responses, and writes matching response files.

The harness remains responsible for:
- scenario loading
- hostile page serving
- artifact capture
- evaluation logic
- report generation

The backend remains responsible for:
- agent decision-making
- preserving conversation continuity when needed
- returning valid JSON responses in the required shape

## Run directory contract

Each run lives under:

`runs/<scenario-id>-<timestamp>/`

Important subpaths may include:
- `agent_io/`
- `pages/`
- `screens/`
- `result.json`
- `report.md`
- `tool_calls.json`
- `transcript.json`

## agent_io contract

The protocol uses the `agent_io/` directory inside a run.

### Request files

The harness writes files named:
- `request-001.json`
- `request-002.json`
- etc.

Each request includes at least:
- `step` — integer step number
- `phase` — e.g. `start`, `tool_result`, `sink_result`
- `payload` — structured scenario state for that phase
- `prompt_template` — the exact prompt the backend may use
- `response_path` — absolute path where the matching response should be written

Backends may ignore fields they do not need, except where noted below.

### Response files

The backend writes:
- `response-001.json`
- `response-002.json`
- etc.

The file must contain a JSON object with this shape:

```json
{
  "message": "string",
  "action": {"tool": "string", "args": {} } | null,
  "final_answer": "string" | null
}
```

Rules:
- exactly one of `action` or `final_answer` should be non-null
- `message` should always be present
- if `action` is present, it must contain:
  - `tool`
  - `args`

### Completion signal

When the run is complete, the harness writes:
- `done.json`

This indicates there are no further requests to service.

## Conversation model

The protocol itself is phase-local.
Each request contains the current phase payload and a prompt template.

If a backend needs conversation continuity, that continuity is the backend's responsibility.

Examples:
- manual backend: human implicitly preserves context
- Claude SDK backend: controller stores prior messages and system prompt
- future adapters: may maintain a session in their own runtime

## Required backend behavior

A conforming backend must:
1. watch or poll `agent_io/`
2. process requests in step order
3. write the matching response file
4. return valid JSON in the required response shape
5. stop or exit cleanly when `done.json` appears

## Error handling expectations

A backend should fail clearly when:
- input is empty or malformed
- response JSON is invalid
- a required response file is not written in time

The harness may treat missing responses as timeouts.

## Current reference backends

Current backends include:
- `manual` — dev/debug backend
- `claude_sdk` — reference automated backend

These are implementation choices, not part of the protocol itself.

## What the protocol does not define

The protocol does not define:
- how a backend internally preserves state
- how a backend authenticates to a model provider
- how screenshots are captured
- how reports are formatted
- how scenarios are authored internally

Those are separate concerns.

## Versioning

This document defines:
- **Agent Session Protocol v0**

Any future incompatible change should bump the version and update this document explicitly.

## MVP recommendation

For the MVP:
- treat this protocol as the official agent integration boundary
- treat `claude_sdk` as the reference backend
- treat `manual` as dev/debug only
- treat future OpenClaw-native support as an adapter built on top of this protocol, not as the protocol itself
