from __future__ import annotations

from web_safety_eval.tui.events import RunEvent
from web_safety_eval.tui.state import AppState, apply_event


def test_apply_event_sequence_updates_run_state():
    state = AppState()
    apply_event(state, RunEvent(run_id='pi-body-text-001-20260420T000000Z', ts=1.0, kind='run_started', data={'scenario_id': 'pi-body-text-001'}))
    apply_event(state, RunEvent(run_id='pi-body-text-001-20260420T000000Z', ts=2.0, kind='tool_called', data={'tool': 'browser.fetch'}))
    apply_event(state, RunEvent(run_id='pi-body-text-001-20260420T000000Z', ts=3.0, kind='run_completed', data={'outcome': 'failed', 'failure_count': 1}))
    rs = state.runs['pi-body-text-001']
    assert rs.status == 'completed'
    assert rs.last_tool == 'browser.fetch'
    assert rs.outcome == 'failed'
