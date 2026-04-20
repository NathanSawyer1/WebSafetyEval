from __future__ import annotations

import pytest

pytest.importorskip('textual')

from web_safety_eval.tui.app import WebSafetyEvalApp


@pytest.mark.asyncio
async def test_app_boots_and_lists_scenarios():
    app = WebSafetyEvalApp(backend='mock', agent='')
    async with app.run_test() as pilot:
        table = app.screen.query_one('#scenarios')
        assert table.row_count >= 6
