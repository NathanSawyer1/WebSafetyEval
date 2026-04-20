from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class FailureSignal:
    type: str
    description: str
    evidence_ref: str | None = None


@dataclass
class ToolCall:
    step: int
    tool: str
    args: dict[str, Any]
    result: dict[str, Any]


@dataclass
class RunResult:
    scenario_id: str
    outcome: str
    failure_signals: list[FailureSignal] = field(default_factory=list)
    final_answer: str = ""
    category: str | None = None
    severity_if_failed: str | None = None
    success_description: str | None = None
    agent: dict[str, Any] | None = None
    run_dir: Path | None = None
    report_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["run_dir"] = str(self.run_dir) if self.run_dir else None
        data["report_path"] = str(self.report_path) if self.report_path else None
        return data
