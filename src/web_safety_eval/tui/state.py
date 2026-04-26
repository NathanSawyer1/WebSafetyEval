from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .events import RunEvent

Status = Literal["pending", "running", "cancelling", "completed", "cancelled", "error"]


@dataclass
class RunState:
    scenario_id: str
    status: Status = "pending"
    run_dir: Path | None = None
    current_step: int = 0
    last_tool: str | None = None
    outcome: str | None = None
    failure_count: int = 0
    started_at: float | None = None
    ended_at: float | None = None
    error: str | None = None


@dataclass
class AppState:
    backend: str = "openclaw"
    agent: str = ""
    runs: dict[str, RunState] = field(default_factory=dict)
    cancel_tokens: dict[str, threading.Event] = field(default_factory=dict)

    def ensure(self, scenario_id: str) -> RunState:
        if scenario_id not in self.runs:
            self.runs[scenario_id] = RunState(scenario_id=scenario_id)
        return self.runs[scenario_id]


def apply_event(state: AppState, evt: RunEvent) -> None:
    sid = evt.data.get("scenario_id") or evt.run_id.rsplit("-", 1)[0]
    rs = state.ensure(sid)
    if evt.kind == "run_started":
        rs.status = "running"
        rs.run_dir = Path("runs") / evt.run_id
        rs.started_at = evt.ts
        rs.current_step = 0
        rs.outcome = None
        rs.failure_count = 0
        rs.error = None
    elif evt.kind == "step_started":
        rs.current_step = int(evt.data.get("step", 0))
    elif evt.kind == "tool_called":
        rs.last_tool = evt.data.get("tool")
    elif evt.kind == "run_completed":
        rs.status = "completed"
        rs.outcome = evt.data.get("outcome")
        rs.failure_count = int(evt.data.get("failure_count", 0))
        rs.ended_at = evt.ts
    elif evt.kind == "run_cancelled":
        rs.status = "cancelled"
        rs.outcome = "cancelled"
        rs.ended_at = evt.ts
