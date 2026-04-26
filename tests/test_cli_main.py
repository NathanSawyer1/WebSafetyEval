from __future__ import annotations

import json
import runpy
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest

from web_safety_eval import __main__ as cli
from web_safety_eval.models import FailureSignal, RunResult


class _Completed:
    def __init__(self, stdout: str):
        self.stdout = stdout


def test_list_scenarios_outputs_known_scenario(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "list-scenarios"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    output = buf.getvalue()
    assert "pi-body-text-001" in output


def test_list_agents_outputs_available_agents(monkeypatch):
    monkeypatch.setattr(cli.subprocess, "run", lambda *args, **kwargs: _Completed(json.dumps([{"id": "main", "name": "Main"}, {"id": "coder", "name": "Coder"}])))
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "list-agents"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    assert buf.getvalue().splitlines() == ["main", "coder"]


def test_list_agents_json_outputs_structured_agents(monkeypatch):
    monkeypatch.setattr(cli.subprocess, "run", lambda *args, **kwargs: _Completed(json.dumps([{"id": "main", "name": "Main"}, {"id": "coder", "name": "Coder"}])))
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "list-agents", "--json"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    assert json.loads(buf.getvalue()) == {"agents": ["main", "coder"]}


def test_quickstart_outputs_copy_paste_examples(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "quickstart"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    output = buf.getvalue()
    assert "web-safety-eval list-scenarios" in output
    assert "web-safety-eval list-agents" in output
    assert "web-safety-eval explain-results" in output


def test_agent_help_outputs_openclaw_guidance(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "agent-help"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    output = buf.getvalue()
    assert "Use this tool when someone asks to test an OpenClaw agent" in output
    assert "list-agents" in output


def test_validate_scenario_outputs_ok(monkeypatch):
    monkeypatch.setattr(cli, "validate_all_scenarios", lambda: {"a-scenario": []})
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "validate-scenario"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)

    cli.main()

    assert "Validated all scenarios: ok" in buf.getvalue()


def test_validate_scenario_exits_nonzero_on_errors(monkeypatch):
    monkeypatch.setattr(cli, "validate_scenario", lambda name: {"bad-scenario": ["bad-scenario: broken"]}[name])
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "validate-scenario", "bad-scenario"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 1
    assert "bad-scenario: broken" in buf.getvalue()


def test_explain_results_outputs_outcome_meaning(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "explain-results"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    output = buf.getvalue()
    assert "failed:" in output
    assert "did_not_fail:" in output
    assert "report.md" in output


def test_no_args_prints_help_and_quickstart_hint(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["web-safety-eval"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    output = buf.getvalue()
    assert "usage:" in output
    assert "Try: web-safety-eval quickstart" in output


def test_run_json_outputs_single_result(monkeypatch, tmp_path):
    monkeypatch.setenv("WEB_SAFETY_DEV", "1")
    result = RunResult(
        scenario_id="pi-body-text-001",
        outcome="failed",
        failure_signals=[FailureSignal(type="tool_call_match", description="sent a secret", evidence_ref="tool_calls.json (entry 1)")],
        run_dir=tmp_path / "runs/pi-body-text-001-123",
        report_path=tmp_path / "runs/pi-body-text-001-123/report.md",
    )
    monkeypatch.setattr(cli, "run_named_scenario", lambda name, runs_dir=None: result)
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "run", "--scenario", "pi-body-text-001", "--backend", "mock", "--json"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)

    cli.main()

    payload = json.loads(buf.getvalue())
    assert payload["scenario_id"] == "pi-body-text-001"
    assert payload["outcome"] == "failed"
    assert payload["run_dir"].endswith("pi-body-text-001-123")
    assert payload["report_path"].endswith("report.md")
    assert payload["failure_signals"][0]["evidence_ref"] == "tool_calls.json (entry 1)"


def test_backend_help_hides_mock_without_dev_mode(monkeypatch):
    monkeypatch.delenv("WEB_SAFETY_DEV", raising=False)
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "run", "--help"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    output = buf.getvalue()
    assert "{openclaw,openclaw_session}" in output
    assert "mock" not in output


def test_backend_help_shows_mock_in_dev_mode(monkeypatch):
    monkeypatch.setenv("WEB_SAFETY_DEV", "1")
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "run", "--help"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    assert "{mock,openclaw,openclaw_session}" in buf.getvalue()


def test_run_rejects_unknown_openclaw_agent(monkeypatch):
    monkeypatch.setattr(cli.subprocess, "run", lambda *args, **kwargs: _Completed(json.dumps([{"id": "main", "name": "Main"}, {"id": "coder", "name": "Coder"}])))
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "run", "--scenario", "pi-body-text-001", "--backend", "openclaw", "--agent", "codex"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2


def test_run_all_json_outputs_results_and_summary(monkeypatch, tmp_path):
    monkeypatch.setenv("WEB_SAFETY_DEV", "1")
    results = {
        "a-scenario": RunResult(
            scenario_id="a-scenario",
            outcome="failed",
            run_dir=tmp_path / "runs/a-scenario-1",
            report_path=tmp_path / "runs/a-scenario-1/report.md",
        ),
        "b-scenario": RunResult(
            scenario_id="b-scenario",
            outcome="did_not_fail",
            run_dir=tmp_path / "runs/b-scenario-1",
            report_path=tmp_path / "runs/b-scenario-1/report.md",
        ),
    }
    monkeypatch.setattr(cli, "scenario_names", lambda: ["a-scenario", "b-scenario"])
    monkeypatch.setattr(cli, "run_named_scenario", lambda name, runs_dir=None: results[name])
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "run-all", "--backend", "mock", "--json"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)

    cli.main()

    payload = json.loads(buf.getvalue())
    assert [item["scenario_id"] for item in payload["results"]] == ["a-scenario", "b-scenario"]
    assert payload["summary"] == {"failed": 1, "did_not_fail": 1, "total": 2}


def test_run_all_script_delegates_to_cli(monkeypatch, tmp_path):
    monkeypatch.setenv("WEB_SAFETY_DEV", "1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["run_all.py", "--backend", "mock"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "run_all.py"), run_name="__main__")
    output = buf.getvalue()
    assert "Running all scenarios with backend=mock" in output
    assert "Summary:" in output
    assert "web-safety-eval explain-results" in output
