from __future__ import annotations

import json

import pytest

from web_safety_eval.session_controller import SessionController


class StubBackend:
    def respond(self, phase: str, payload: dict, prompt: str) -> str:
        return '{"ok": true}'


def test_service_once_rejects_response_path_escape(tmp_path):
    agent_io = tmp_path / "agent_io"
    agent_io.mkdir()
    request_path = agent_io / "request-001.json"
    request_path.write_text(json.dumps({
        "phase": "start",
        "prompt_template": "hello",
        "payload": {},
        "step": 1,
        "response_path": str(tmp_path / "outside.json"),
    }), encoding="utf-8")

    controller = SessionController(agent_io_dir=agent_io, backend=StubBackend())
    with pytest.raises(ValueError, match="escapes agent_io_dir"):
        controller.service_once()


def test_service_once_writes_default_response_inside_agent_io(tmp_path):
    agent_io = tmp_path / "agent_io"
    agent_io.mkdir()
    request_path = agent_io / "request-001.json"
    request_path.write_text(json.dumps({
        "phase": "start",
        "prompt_template": "hello",
        "payload": {},
        "step": 1,
    }), encoding="utf-8")

    controller = SessionController(agent_io_dir=agent_io, backend=StubBackend())
    assert controller.service_once() is True
    response_path = agent_io / "response-001.json"
    assert response_path.exists()
    assert json.loads(response_path.read_text(encoding="utf-8")) == {"ok": True}
