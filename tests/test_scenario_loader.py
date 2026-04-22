from __future__ import annotations

import json

import pytest

from web_safety_eval.scenario_loader import load_scenario


def test_load_scenario_validates_required_fields(tmp_path, monkeypatch):
    from web_safety_eval import scenario_loader

    scenarios = tmp_path / "scenarios"
    case_dir = scenarios / "broken-001"
    case_dir.mkdir(parents=True)
    (case_dir / "scenario.json").write_text(json.dumps({
        "id": "broken-001",
        "category": "prompt_injection",
        "entry_page": "index.html",
        "system_prompt": "sys",
        "user_task": "task",
        "tools": [{"name": "browser.fetch"}],
        "failure_conditions": [],
    }), encoding="utf-8")

    monkeypatch.setattr(scenario_loader, "SCENARIOS_DIR", scenarios)

    with pytest.raises(ValueError, match="severity_if_failed"):
        load_scenario("broken-001")


def test_load_scenario_rejects_unknown_failure_condition_type(tmp_path, monkeypatch):
    from web_safety_eval import scenario_loader

    scenarios = tmp_path / "scenarios"
    case_dir = scenarios / "broken-002"
    case_dir.mkdir(parents=True)
    (case_dir / "scenario.json").write_text(json.dumps({
        "id": "broken-002",
        "category": "prompt_injection",
        "severity_if_failed": "high",
        "entry_page": "index.html",
        "system_prompt": "sys",
        "user_task": "task",
        "tools": [{"name": "browser.fetch"}],
        "failure_conditions": [{"type": "made_up", "description": "nope"}],
    }), encoding="utf-8")

    monkeypatch.setattr(scenario_loader, "SCENARIOS_DIR", scenarios)

    with pytest.raises(ValueError, match="made_up"):
        load_scenario("broken-002")
