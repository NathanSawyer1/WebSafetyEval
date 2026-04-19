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
