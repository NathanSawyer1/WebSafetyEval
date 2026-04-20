from __future__ import annotations

import json
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown, Static, TabbedContent, TabPane

from ..runs_index import read_run_artifacts


class ResultDetailScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(self, run_dir: Path) -> None:
        super().__init__()
        self.run_dir = run_dir
        self.artifacts = read_run_artifacts(run_dir)

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Report", id="report-tab"):
                yield Markdown(self.artifacts["report"] or "No report.md found", id="report")
            with TabPane("Tool calls", id="tool-calls-tab"):
                pretty = json.dumps(self.artifacts["tool_calls"], indent=2)
                yield Static(pretty or "[]", id="tool-calls")
            with TabPane("Transcript", id="transcript-tab"):
                pretty = json.dumps(self.artifacts["transcript"], indent=2)
                yield Static(pretty or "[]", id="transcript")
            with TabPane("Artifacts", id="artifacts-tab"):
                yield Static(str(self.artifacts["run_dir"]), id="artifacts")
        yield Footer()
