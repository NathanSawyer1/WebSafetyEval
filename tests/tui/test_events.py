from __future__ import annotations

from web_safety_eval.tui.events import parse_line


def test_parse_line_accepts_valid_event():
    evt = parse_line('run-1', '{"ts":1.0,"kind":"run_started","scenario_id":"pi-body-text-001"}')
    assert evt is not None
    assert evt.kind == 'run_started'


def test_parse_line_ignores_unknown_kind():
    assert parse_line('run-1', '{"ts":1.0,"kind":"wat"}') is None


def test_parse_line_ignores_torn_json():
    assert parse_line('run-1', '{"ts":1.0') is None
