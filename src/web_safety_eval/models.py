from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FailureConditionType(str, Enum):
    TOOL_CALL_MATCH = "tool_call_match"
    FINAL_ANSWER_MATCH = "final_answer_match"
    SECRET_MATCH_IN_TOOL_ARGS = "secret_match_in_tool_args"
    SECRET_MATCH_IN_FINAL_ANSWER = "secret_match_in_final_answer"
    DISALLOWED_TOOL_CALL = "disallowed_tool_call"


class FailureCondition(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    type: FailureConditionType
    description: str
    tool: str | None = None
    url_contains: str | None = None
    answer_contains: str | None = None
    allowed_tools: list[str] = Field(default_factory=list)


class ScenarioDef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    category: str
    severity_if_failed: str
    entry_page: str
    system_prompt: str
    user_task: str
    version: str | int | None = None
    tools: list[dict[str, Any]] = Field(default_factory=list)
    max_steps: int = 5
    failure_conditions: list[FailureCondition]
    planted_secrets: list[str] = Field(default_factory=list)
    success: dict[str, Any] = Field(default_factory=dict)
    scenario_dir: Path | None = None


@dataclass
class FailureSignal:
    type: str
    description: str
    evidence_ref: str | None = None
    matched_content: str | None = None


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
