from __future__ import annotations

import json

from web_safety_eval.openclaw_cli_agent import OpenClawCliAgent


class _Completed:
    def __init__(self, stdout: str, returncode: int = 0, stderr: str = "") -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr


def test_openclaw_cli_agent_parses_json_envelope(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(args, text, capture_output, timeout, check):
        calls.append(args)
        return _Completed(json.dumps({
            "result": {
                "payloads": [
                    {
                        "text": '{"message":"Requesting the starting page.","action":{"tool":"browser.fetch","args":{"page":"reviews.html"}},"final_answer":null}'
                    }
                ]
            }
        }))

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/openclaw")
    agent = OpenClawCliAgent(timeout_seconds=5)
    response = agent.start("system", "task", [{"name": "browser.fetch"}])

    assert response.message == "Requesting the starting page."
    assert response.action == {"tool": "browser.fetch", "args": {"page": "reviews.html"}}
    assert response.final_answer is None
    assert calls[0][0:3] == ["openclaw", "agent", "--session-id"]
    assert "--json" in calls[0]
    assert "--message" in calls[0]


def test_openclaw_cli_agent_raises_on_nonzero_exit(monkeypatch):
    def fake_run(args, text, capture_output, timeout, check):
        return _Completed("", returncode=1, stderr="boom")

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/openclaw")
    agent = OpenClawCliAgent(timeout_seconds=5)

    try:
        agent.start("system", "task", [{"name": "browser.fetch"}])
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        assert "boom" in str(exc)


def test_openclaw_cli_agent_parses_wrapped_json_without_retry(monkeypatch):
    calls: list[str] = []

    def fake_run(args, text, capture_output, timeout, check):
        calls.append(args[-1])
        return _Completed(json.dumps({
            "result": {
                "payloads": [
                    {
                        "text": 'Here is the result:\n{"message":"Requesting the starting page.","action":{"tool":"browser.fetch","args":{"page":"reviews.html"}},"final_answer":null}\nThanks!'
                    }
                ]
            }
        }))

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/openclaw")
    agent = OpenClawCliAgent(timeout_seconds=5)
    response = agent.start("system", "task", [{"name": "browser.fetch"}])

    assert response.action == {"tool": "browser.fetch", "args": {"page": "reviews.html"}}
    assert len(calls) == 1


def test_openclaw_cli_agent_retries_on_invalid_json(monkeypatch):
    calls: list[str] = []
    responses = iter([
        _Completed(json.dumps({
            "result": {
                "payloads": [
                    {
                        "text": 'not valid json at all'
                    }
                ]
            }
        })),
        _Completed(json.dumps({
            "result": {
                "payloads": [
                    {
                        "text": '{"message":"Requesting the starting page.","action":{"tool":"browser.fetch","args":{"page":"reviews.html"}},"final_answer":null}'
                    }
                ]
            }
        })),
    ])

    def fake_run(args, text, capture_output, timeout, check):
        calls.append(args[-1])
        return next(responses)

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/openclaw")
    agent = OpenClawCliAgent(timeout_seconds=5)
    response = agent.start("system", "task", [{"name": "browser.fetch"}])

    assert response.action == {"tool": "browser.fetch", "args": {"page": "reviews.html"}}
    assert len(calls) == 2
    assert "Your previous response was not valid JSON" in calls[1]


def test_openclaw_cli_agent_requires_openclaw_binary(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)

    try:
        OpenClawCliAgent(timeout_seconds=5)
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        assert "Could not find `openclaw` on PATH" in str(exc)


def test_run_demo_flag_agent_overrides_env(monkeypatch, tmp_path):
    import runpy
    import sys
    from io import StringIO
    from pathlib import Path

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("WEB_SAFETY_OPENCLAW_AGENT", "from-env")
    monkeypatch.setattr(sys, "argv", ["run_demo.py", "--backend", "mock", "--agent", "from-flag", "--scenario", "pi-body-text-001"])

    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "run_demo.py"), run_name="__main__")

    output = buf.getvalue()
    assert "agent=from-flag" in output


def test_openclaw_cli_agent_omits_agent_flag_when_unset(monkeypatch):
    import subprocess

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/openclaw")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        raise RuntimeError("stop after capturing command")

    monkeypatch.setattr(subprocess, "run", fake_run)
    agent = OpenClawCliAgent(timeout_seconds=5)
    try:
        agent._run_turn("test")
    except RuntimeError as exc:
        assert str(exc) == "stop after capturing command"
    else:
        raise AssertionError("Expected fake_run sentinel")
    assert "--agent" not in calls[0]


def test_openclaw_cli_agent_uses_configured_agent_flag(monkeypatch):
    import subprocess

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/openclaw")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        raise RuntimeError("stop after capturing command")

    monkeypatch.setattr(subprocess, "run", fake_run)
    agent = OpenClawCliAgent(timeout_seconds=5, agent_name="codex")
    try:
        agent._run_turn("test")
    except RuntimeError as exc:
        assert str(exc) == "stop after capturing command"
    else:
        raise AssertionError("Expected fake_run sentinel")

    cmd = calls[0]
    assert "--agent" in cmd
    idx = cmd.index("--agent")
    assert cmd[idx + 1] == "codex"
    assert "--json" in cmd
    assert "--session-id" in cmd
