from __future__ import annotations

import pytest

pytest.importorskip("textual")

from web_safety_eval.tui.app import WebSafetyEvalApp
from web_safety_eval.tui.state import RunState


@pytest.mark.asyncio
async def test_app_boots_and_lists_scenarios():
    app = WebSafetyEvalApp(backend="mock", agent="")
    async with app.run_test() as pilot:
        table = app.screen.query_one("#scenarios")
        assert table.row_count >= 6


@pytest.mark.asyncio
async def test_open_selected_pushes_result_detail(tmp_path):
    run_dir = tmp_path / "pi-body-text-001-20260420T000000Z"
    run_dir.mkdir()
    (run_dir / "report.md").write_text("# Report\n", encoding="utf-8")
    (run_dir / "tool_calls.json").write_text("[]", encoding="utf-8")
    (run_dir / "transcript.json").write_text("[]", encoding="utf-8")

    app = WebSafetyEvalApp(backend="mock", agent="")
    app.state.runs["pi-body-text-001"] = RunState(
        scenario_id="pi-body-text-001",
        status="completed",
        run_dir=run_dir,
        outcome="did_not_fail",
    )

    async with app.run_test() as pilot:
        await pilot.press("enter")
        report = app.screen.query_one("#report")
        assert "Report" in str(report.renderable)
