from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

EVENT_KINDS = frozenset({
    "run_started",
    "agent_turn",
    "step_started",
    "tool_called",
    "screenshot_captured",
    "run_completed",
    "run_cancelled",
})


@dataclass(frozen=True, slots=True)
class RunEvent:
    run_id: str
    ts: float
    kind: str
    data: dict[str, Any]


def parse_line(run_id: str, line: str) -> RunEvent | None:
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None
    kind = obj.pop("kind", None)
    ts = obj.pop("ts", 0.0)
    if kind not in EVENT_KINDS:
        return None
    return RunEvent(run_id=run_id, ts=float(ts), kind=kind, data=obj)


def read_all(run_dir: Path) -> Iterator[RunEvent]:
    path = run_dir / "events.jsonl"
    if not path.exists():
        return
    run_id = run_dir.name
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            evt = parse_line(run_id, line.rstrip("\n"))
            if evt is not None:
                yield evt
