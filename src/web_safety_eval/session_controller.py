from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import socket
import urllib.error
import urllib.request


class ControllerBackend(Protocol):
    def respond(self, phase: str, payload: dict[str, Any], prompt: str) -> str: ...


@dataclass
class ManualBackend:
    def respond(self, phase: str, payload: dict[str, Any], prompt: str) -> str:
        step_hint = payload.get("page") or payload.get("url") or payload.get("user_task") or "(no summary)"
        print(f"\n=== REQUEST {phase.upper()} START ===\n")
        print(f"Summary: {step_hint}")
        print()
        print(prompt)
        print("\n=== REQUEST END ===\n")
        print("Paste JSON response. Finish with a blank line.")
        print("Single-line JSON is also accepted.")

        lines: list[str] = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line.strip():
                break
            lines.append(line)
            if len(lines) == 1 and line.strip().startswith("{") and line.strip().endswith("}"):
                break
        return "\n".join(lines).strip()


class ClaudeSdkBackend:
    def __init__(self, model: str | None = None) -> None:
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic package is required for backend=claude_sdk") from exc
        self.anthropic = anthropic.Anthropic()
        self.model = model or os.environ.get("WEB_SAFETY_CLAUDE_MODEL", "claude-sonnet-4-5")
        self.history: list[dict[str, str]] = []
        self.system_prompt: str | None = None

    def respond(self, phase: str, payload: dict[str, Any], prompt: str) -> str:
        if phase == "start":
            self.history = []
            self.system_prompt = payload.get("system_prompt")
        self.history.append({"role": "user", "content": prompt})
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=800,
            system=self.system_prompt or "",
            messages=self.history,
        )
        text_parts: list[str] = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
        text = "\n".join(text_parts).strip()
        self.history.append({"role": "assistant", "content": text})
        return text


class OpenClawHttpBackend:
    REQUEST_TIMEOUT_SECONDS = 30

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("OPENCLAW_HTTP_URL") or "").rstrip("/")
        if not self.base_url:
            raise RuntimeError("OPENCLAW_HTTP_URL is required for backend=openclaw_http")
        self.session_id: str | None = None

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"content-type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.REQUEST_TIMEOUT_SECONDS) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenClaw HTTP error {exc.code}: {body}") from exc
        except TimeoutError as exc:
            raise RuntimeError(
                f"Timed out after {self.REQUEST_TIMEOUT_SECONDS}s reaching OpenClaw HTTP backend at {url}"
            ) from exc
        except socket.timeout as exc:
            raise RuntimeError(
                f"Timed out after {self.REQUEST_TIMEOUT_SECONDS}s reaching OpenClaw HTTP backend at {url}"
            ) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise RuntimeError(
                    f"Timed out after {self.REQUEST_TIMEOUT_SECONDS}s reaching OpenClaw HTTP backend at {url}"
                ) from exc
            if isinstance(exc.reason, socket.timeout):
                raise RuntimeError(
                    f"Timed out after {self.REQUEST_TIMEOUT_SECONDS}s reaching OpenClaw HTTP backend at {url}"
                ) from exc
            raise RuntimeError(f"Could not reach OpenClaw HTTP backend at {url}: {exc}") from exc
        return json.loads(body or "{}")

    def _ensure_session(self) -> None:
        if self.session_id is not None:
            return
        payload = self._request("POST", "/v0/agent/sessions", {})
        self.session_id = payload["session_id"]

    def respond(self, phase: str, payload: dict[str, Any], prompt: str) -> str:
        self._ensure_session()
        assert self.session_id is not None
        response = self._request(
            "POST",
            f"/v0/agent/sessions/{self.session_id}/step",
            {
                "phase": phase,
                "payload": payload,
                "prompt": prompt,
            },
        )
        return json.dumps(response)

    def close(self) -> None:
        if self.session_id is None:
            return
        try:
            self._request("DELETE", f"/v0/agent/sessions/{self.session_id}")
        finally:
            self.session_id = None


class SessionController:
    def __init__(self, agent_io_dir: Path, backend: ControllerBackend, poll_interval: float = 0.5) -> None:
        self.agent_io_dir = agent_io_dir
        self.backend = backend
        self.poll_interval = poll_interval
        self.agent_io_dir.mkdir(parents=True, exist_ok=True)
        self.processed_steps = 0
        self.last_step: int | None = None

    def _request_paths(self) -> list[Path]:
        return sorted(self.agent_io_dir.glob("request-*.json"))

    def _extract_json_span(self, raw: str) -> str:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end < start:
            if not raw.strip():
                raise ValueError(
                    "Empty response received from controller backend. Paste a JSON object and end input with Ctrl-D."
                )
            raise ValueError(f"Could not parse JSON from response: {raw}")
        return raw[start:end + 1]

    def service_once(self) -> bool:
        for request_path in self._request_paths():
            request = json.loads(request_path.read_text(encoding="utf-8"))
            response_path = Path(request.get("response_path") or self.agent_io_dir / request_path.name.replace("request-", "response-", 1))
            if response_path.exists():
                continue
            phase = request.get("phase", "")
            prompt = request["prompt_template"]
            payload = request.get("payload", {})
            self.last_step = int(request.get("step", 0))
            raw_response = self.backend.respond(phase=phase, payload=payload, prompt=prompt)
            try:
                normalized = self._extract_json_span(raw_response)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid controller response for request-{self.last_step:03d}.json: {exc}"
                ) from exc
            response_path.write_text(normalized, encoding="utf-8")
            self.processed_steps += 1
            return True
        return False

    def run(self) -> None:
        try:
            while True:
                done_path = self.agent_io_dir / "done.json"
                if done_path.exists():
                    close = getattr(self.backend, "close", None)
                    if callable(close):
                        close()
                    run_id = self.agent_io_dir.parent.name
                    print(f"processed {self.processed_steps} steps in run {run_id}")
                    return
                serviced = self.service_once()
                if not serviced:
                    time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print(f"interrupted, last request step: {self.last_step}")
            raise


def _find_latest_agent_io(root: Path, max_age_seconds: int = 300) -> Path:
    now = time.time()
    candidates: list[Path] = []
    for run_dir in root.glob("*"):
        agent_io = run_dir / "agent_io"
        if not agent_io.exists():
            continue
        created_recently = (now - run_dir.stat().st_mtime) <= max_age_seconds
        if created_recently:
            candidates.append(agent_io)
    if not candidates:
        raise FileNotFoundError(f"No recent agent_io directories found under {root}")
    candidates.sort(key=lambda p: p.parent.stat().st_mtime, reverse=True)
    return candidates[0]


def build_backend(name: str, model: str | None = None) -> ControllerBackend:
    normalized = name.strip().lower()
    if normalized == "manual":
        return ManualBackend()
    if normalized == "claude_sdk":
        return ClaudeSdkBackend(model=model)
    if normalized == "openclaw_http":
        return OpenClawHttpBackend()
    raise ValueError(f"Unknown backend: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Service web-safety-eval agent_io requests")
    parser.add_argument("--run-dir", help="Path to run directory containing agent_io/")
    parser.add_argument("--agent-io-dir", help="Path to agent_io directory")
    parser.add_argument("--runs-dir", default=str(Path(__file__).resolve().parents[2] / "runs"))
    parser.add_argument("--backend", default=os.environ.get("WEB_SAFETY_CONTROLLER_BACKEND", "manual"))
    parser.add_argument("--model", default=os.environ.get("WEB_SAFETY_CLAUDE_MODEL"))
    parser.add_argument("--poll-interval", type=float, default=0.5)
    args = parser.parse_args()

    if args.run_dir:
        agent_io_dir = Path(args.run_dir) / "agent_io"
    elif args.agent_io_dir:
        agent_io_dir = Path(args.agent_io_dir)
    else:
        agent_io_dir = _find_latest_agent_io(Path(args.runs_dir))

    backend = build_backend(args.backend, model=args.model)
    controller = SessionController(agent_io_dir=agent_io_dir, backend=backend, poll_interval=args.poll_interval)
    controller.run()


if __name__ == "__main__":
    main()
