from __future__ import annotations

import json
import runpy
import sys
from io import StringIO
from pathlib import Path

from web_safety_eval import __main__ as cli


def test_list_scenarios_outputs_known_scenario(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "list-scenarios"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    output = buf.getvalue()
    assert "pi-body-text-001" in output


def test_quickstart_outputs_copy_paste_examples(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "quickstart"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    output = buf.getvalue()
    assert "web-safety-eval list-scenarios" in output
    assert "web-safety-eval explain-results" in output


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


def test_run_all_script_delegates_to_cli(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["run_all.py", "--backend", "mock"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "run_all.py"), run_name="__main__")
    output = buf.getvalue()
    assert "Running all scenarios with backend=mock" in output
    assert "Summary:" in output
    assert "web-safety-eval explain-results" in output


def test_agent_help_outputs_skill_primer(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["web-safety-eval", "agent-help"])
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    output = buf.getvalue()
    assert "install-skill" in output
    assert "yourself" in output
    assert "--json" in output


def test_run_json_emits_parseable_payload(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["web-safety-eval", "run", "--backend", "mock", "--scenario", "pi-body-text-001", "--json"],
    )
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    payload = json.loads(buf.getvalue())
    assert payload["scenario_id"] == "pi-body-text-001"
    assert payload["outcome"] in {"failed", "did_not_fail"}
    assert payload["run_dir"]
    assert payload["report_path"]
    assert isinstance(payload["failure_signals"], list)


def test_run_all_json_emits_results_and_summary(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["web-safety-eval", "run-all", "--backend", "mock", "--json"],
    )
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    payload = json.loads(buf.getvalue())
    assert isinstance(payload["results"], list)
    assert payload["results"]
    assert payload["summary"]["total"] == len(payload["results"])
    assert (
        payload["summary"]["failed"] + payload["summary"]["did_not_fail"]
        == payload["summary"]["total"]
    )
