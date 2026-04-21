from __future__ import annotations

import threading

import pytest

pytest.importorskip("textual")

from web_safety_eval.tui.app import DashboardScreen, WebSafetyEvalApp
from web_safety_eval.tui.state import RunState


@pytest.mark.asyncio
async def test_app_boots_and_lists_scenarios():
    app = WebSafetyEvalApp(backend="mock", agent="")
    async with app.run_test() as pilot:
        table = app.screen.query_one("#scenarios")
        assert table.row_count >= 6


@pytest.mark.asyncio
@pytest.mark.xfail(reason="screen switching needs mocking fix")
async def test_open_selected_pushes_result_detail(tmp_path, monkeypatch):
    run_dir = tmp_path / "pi-body-text-001-20260420T000000Z"
    run_dir.mkdir()
    (run_dir / "report.md").write_text("# Report\n", encoding="utf-8")
    (run_dir / "tool_calls.json").write_text('[{"step": 1, "tool": "browser.fetch", "args": {"page": "reviews.html"}, "result": {"kind": "page"}}]', encoding="utf-8")
    (run_dir / "transcript.json").write_text('[{"role": "agent", "payload": {"message": "hi"}}]', encoding="utf-8")

    # Patching strategy: patch at app.py namespace where it's imported
    # This needs to happen BEFORE WebSafetyEvalApp is instantiated
    import web_safety_eval.tui.app as app_module
    
    # Store originals
    orig_list = app_module.list_scenarios
    orig_meta = app_module.load_scenario_meta
    
    def mock_list():
        return ["pi-body-text-001"]
    
    def mock_meta(sid):
        return {"id": sid, "category": "test", "severity": "low"}
    
    # Patch in app_module namespace
    monkeypatch.setattr(app_module, "list_scenarios", mock_list)
    monkeypatch.setattr(app_module, "load_scenario_meta", mock_meta)

    # Create app AFTER patching
    app = WebSafetyEvalApp(backend="mock", agent="")
    # Pre-populate the completed run
    app.state.runs["pi-body-text-001"] = RunState(
        scenario_id="pi-body-text-001",
        status="completed",
        run_dir=run_dir,
        outcome="did_not_fail",
    )

    async with app.run_test() as pilot:
        # Now row 0 is pi-body-text-001 with a completed run
        await pilot.press("enter")
        # After enter, we should be on ResultDetailScreen
        report = app.screen.query_one("#report")
        assert "Report" in str(report.renderable)
        # Tab to tool calls tab
        await pilot.press("tab")
        tool_calls = app.screen.query_one("#tool-calls")
        assert "browser.fetch" in str(tool_calls.renderable)


@pytest.mark.asyncio
async def test_run_all_marks_rows_running(monkeypatch):
    app = WebSafetyEvalApp(backend="mock", agent="")

    def fake_run_all(self, backend: str, agent: str):
        for scenario_id in ["fake-system-instruction-001", "indirect-prompt-injection-001"]:
            self.state.ensure(scenario_id).status = "running"
        self._refresh_table()

    monkeypatch.setattr(DashboardScreen, "run_all_scenarios", fake_run_all)

    async with app.run_test() as pilot:
        await pilot.press("a")
        table = app.screen.query_one("#scenarios")
        assert table.get_cell_at((0, 3)) == "running"


@pytest.mark.asyncio
async def test_cancel_selected_marks_row_cancelling():
    app = WebSafetyEvalApp(backend="mock", agent="")
    app.state.runs["fake-system-instruction-001"] = RunState(
        scenario_id="fake-system-instruction-001",
        status="running",
    )
    app.state.cancel_tokens["fake-system-instruction-001"] = threading.Event()

    async with app.run_test() as pilot:
        await pilot.press("c")
        table = app.screen.query_one("#scenarios")
        assert table.get_cell_at((0, 3)) == "cancelling, waiting for current turn"
        assert app.state.cancel_tokens["fake-system-instruction-001"].is_set()


def test_list_openclaw_agents_returns_names():
    from web_safety_eval.tui.runs_index import list_openclaw_agents

    agents = list_openclaw_agents()
    assert isinstance(agents, list)
