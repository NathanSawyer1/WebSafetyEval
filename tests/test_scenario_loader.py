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


def _write_minimal_scenario(scenario_dir, *, entry_page="index.html", url_contains="https://example.com/sink"):
    (scenario_dir / "pages").mkdir(parents=True)
    (scenario_dir / "scenario.json").write_text(json.dumps({
        "id": scenario_dir.name,
        "category": "prompt_injection",
        "severity_if_failed": "medium",
        "entry_page": entry_page,
        "system_prompt": "system",
        "user_task": "task",
        "tools": [{"name": "browser.fetch"}],
        "failure_conditions": [{
            "type": "tool_call_match",
            "description": "sink reached",
            "tool": "browser.fetch",
            "url_contains": url_contains,
        }],
    }), encoding="utf-8")


def test_validate_scenario_accepts_valid_fixture(tmp_path):
    from web_safety_eval.scenario_loader import validate_scenario

    scenario_dir = tmp_path / "valid-001"
    _write_minimal_scenario(scenario_dir)
    (scenario_dir / "pages" / "index.html").write_text("Visit https://example.com/sink", encoding="utf-8")

    assert validate_scenario("valid-001", scenarios_dir=tmp_path) == []


def test_validate_scenario_reports_missing_entry_page_and_dead_url_needle(tmp_path):
    from web_safety_eval.scenario_loader import validate_scenario

    scenario_dir = tmp_path / "broken-001"
    _write_minimal_scenario(scenario_dir, entry_page="missing.html", url_contains="https://missing.example/sink")
    (scenario_dir / "pages" / "index.html").write_text("No matching URL here", encoding="utf-8")

    errors = validate_scenario("broken-001", scenarios_dir=tmp_path)

    assert any("entry_page not found" in error for error in errors)
    assert any("url_contains not found" in error for error in errors)
