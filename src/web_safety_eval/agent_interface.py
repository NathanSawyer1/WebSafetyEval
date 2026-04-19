from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class AgentStartResponse:
    message: str
    action: dict[str, Any] | None = None
    final_answer: str | None = None


class AgentInterface(Protocol):
    def start(self, system_prompt: str, user_task: str, tools: list[dict[str, Any]]) -> AgentStartResponse: ...
    def handle_tool_result(self, tool_result: dict[str, Any]) -> AgentStartResponse: ...
    def handle_sink_result(self, tool_result: dict[str, Any]) -> AgentStartResponse: ...
