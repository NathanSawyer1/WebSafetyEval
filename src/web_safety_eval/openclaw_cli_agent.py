from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from typing import Any

from .agent_interface import AgentStartResponse
from .jsonspan import extract_json_span
from .prompts import build_phase_prompt


class OpenClawCliAgent:
    JSON_RETRY_PROMPT = "Your previous response was not valid JSON. Respond now with ONLY the JSON object, with no prose or markdown."
    OPENCLAW_AGENT_FLAG = "--agent"

    def __init__(self, entry_page: str = "reviews.html", timeout_seconds: int | None = None, use_local: bool | None = None, agent_name: str | None = None) -> None:
        if shutil.which("openclaw") is None:
            raise RuntimeError("Could not find `openclaw` on PATH. Install OpenClaw and ensure the CLI is available before running the evaluator.")
        self.session_id = str(uuid.uuid4())
        self.entry_page = entry_page
        self.timeout_seconds = timeout_seconds or int(os.environ.get("WEB_SAFETY_OPENCLAW_TIMEOUT", "120"))
        self.use_local = use_local if use_local is not None else os.environ.get("WEB_SAFETY_OPENCLAW_LOCAL") == "1"
        self.agent_name = agent_name if agent_name is not None else (os.environ.get("WEB_SAFETY_OPENCLAW_AGENT") or "").strip() or None

    def _invoke(self, prompt: str) -> str:
        args = [
            "openclaw",
            "agent",
            "--session-id",
            self.session_id,
            "--json",
            "--message",
            prompt,
        ]
        if self.use_local:
            args.append("--local")
        if self.agent_name:
            args.extend([self.OPENCLAW_AGENT_FLAG, self.agent_name])

        proc = subprocess.run(
            args,
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"openclaw agent failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
            )

        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Could not parse openclaw agent JSON output: {proc.stdout}") from exc

        payloads = (((envelope.get("result") or {}).get("payloads")) or [])
        return "\n".join(payload.get("text", "") for payload in payloads if payload.get("text")).strip()

    def _run_turn(self, prompt: str) -> AgentStartResponse:
        text = self._invoke(prompt)
        try:
            parsed = json.loads(extract_json_span(text))
        except (ValueError, json.JSONDecodeError):
            text = self._invoke(f"{self.JSON_RETRY_PROMPT}\n\nPrevious response:\n{text}")
            parsed = json.loads(extract_json_span(text))
        return AgentStartResponse(
            message=parsed.get("message", ""),
            action=parsed.get("action"),
            final_answer=parsed.get("final_answer"),
        )

    def start(self, system_prompt: str, user_task: str, tools: list[dict[str, Any]]) -> AgentStartResponse:
        return self._run_turn(build_phase_prompt("start", {
            "system_prompt": system_prompt,
            "user_task": user_task,
            "tools": tools,
            "entry_page": self.entry_page,
        }))

    def describe(self) -> dict[str, Any]:
        return {"backend": "openclaw", "agent": self.agent_name or "<openclaw-default>", "local": self.use_local}

    def handle_tool_result(self, tool_result: dict[str, Any]) -> AgentStartResponse:
        return self._run_turn(build_phase_prompt("tool_result", tool_result))

    def handle_sink_result(self, tool_result: dict[str, Any]) -> AgentStartResponse:
        return self._run_turn(build_phase_prompt("sink_result", tool_result))

    def close(self) -> None:
        return
