from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from .agent_interface import AgentStartResponse
from .jsonspan import extract_json_span
from .prompts import build_phase_prompt


class OpenClawSessionAgent:
    """Blocking file-IPC adapter for real OpenClaw session decisions.

    Python remains the orchestrator. Another OpenClaw-aware controller can watch
    the `agent_io/` directory, forward requests into a real session with
    `sessions_spawn` / `sessions_send`, and write back JSON responses.
    """

    def __init__(self, run_dir: Path, timeout_seconds: int | None = None, poll_interval: float = 1.0) -> None:
        self.run_dir = run_dir
        self.agent_io_dir = run_dir / "agent_io"
        self.agent_io_dir.mkdir(parents=True, exist_ok=True)
        self.step = 0
        self.timeout_seconds = timeout_seconds or int(os.environ.get("WEB_SAFETY_AGENT_TIMEOUT", "600"))
        self.poll_interval = poll_interval

    def _parse_response_text(self, raw: str) -> AgentStartResponse:
        parsed = json.loads(extract_json_span(raw))
        return AgentStartResponse(
            message=parsed.get("message", ""),
            action=parsed.get("action"),
            final_answer=parsed.get("final_answer"),
        )

    def _send(self, phase: str, payload: dict[str, Any]) -> AgentStartResponse:
        self.step += 1
        request_path = self.agent_io_dir / f"request-{self.step:03d}.json"
        response_path = self.agent_io_dir / f"response-{self.step:03d}.json"

        request = {
            "step": self.step,
            "phase": phase,
            "payload": payload,
            "prompt_template": build_phase_prompt(phase, payload),
            "response_path": str(response_path),
        }
        request_path.write_text(json.dumps(request, indent=2), encoding="utf-8")

        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            if response_path.exists():
                raw = response_path.read_text(encoding="utf-8")
                return self._parse_response_text(raw)
            time.sleep(self.poll_interval)

        raise TimeoutError(
            f"Timed out waiting for {response_path.name}. A controller must read {request_path.name} and write the response file."
        )

    def start(self, system_prompt: str, user_task: str, tools: list[dict[str, Any]]) -> AgentStartResponse:
        return self._send("start", {
            "system_prompt": system_prompt,
            "user_task": user_task,
            "tools": tools,
        })

    def handle_tool_result(self, tool_result: dict[str, Any]) -> AgentStartResponse:
        return self._send("tool_result", tool_result)

    def handle_sink_result(self, tool_result: dict[str, Any]) -> AgentStartResponse:
        return self._send("sink_result", tool_result)

    def close(self) -> None:
        done_path = self.agent_io_dir / "done.json"
        done_path.write_text(json.dumps({"done": True, "steps": self.step}, indent=2), encoding="utf-8")
