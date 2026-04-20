from __future__ import annotations

import threading

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Select, Static

from .messages import RunEventMessage
from .runs_index import list_scenarios, load_scenario_meta
from .screens.result_detail import ResultDetailScreen
from .state import AppState, apply_event
from .tail import tail_events
from .worker import run_scenario_worker

CSS = """
Screen { layout: vertical; }
#controls { height: 3; }
#summary { height: 1; }
DataTable { height: 1fr; }
#report, #tool-calls, #transcript, #artifacts { padding: 1; overflow: auto; }
"""


class DashboardScreen(Screen):
    BINDINGS = [
        Binding("r", "run_selected", "Run selected"),
        Binding("a", "run_all", "Run all"),
        Binding("c", "cancel_selected", "Cancel selected"),
        Binding("enter", "open_selected", "Open selected"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="controls"):
            yield Select([(value, value) for value in ["mock", "openclaw", "openclaw_session"]], value=self.state.backend, id="backend")
            yield Input(value=self.state.agent, placeholder="agent", id="agent")
        yield DataTable(id="scenarios")
        yield Static("Use ↑/↓ to select, r to run, a to run all, c to cancel, Enter to open completed runs", id="summary")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#scenarios", DataTable)
        table.cursor_type = "row"
        table.add_columns("id", "category", "severity", "status", "outcome")
        for scenario_id in list_scenarios():
            meta = load_scenario_meta(scenario_id)
            self.state.ensure(scenario_id)
            table.add_row(meta["id"], meta["category"], meta["severity"], "pending", "", key=scenario_id)
        self._refresh_table()
        if table.row_count:
            table.move_cursor(row=0)

    def _selected_scenario_id(self) -> str | None:
        table = self.query_one("#scenarios", DataTable)
        if table.cursor_row is None:
            return None
        return str(table.get_row_at(table.cursor_row)[0])

    def _selected_backend_and_agent(self) -> tuple[str, str]:
        backend = str(self.query_one("#backend", Select).value)
        agent = self.query_one("#agent", Input).value
        self.state.backend = backend
        self.state.agent = agent
        return backend, agent

    def _refresh_table(self) -> None:
        table = self.query_one("#scenarios", DataTable)
        for scenario_id, run_state in self.state.runs.items():
            try:
                row_index = table.get_row_index(scenario_id)
            except Exception:
                continue
            status = run_state.status
            if run_state.status == "running" and run_state.last_tool:
                status = f"running step {run_state.current_step} {run_state.last_tool}"
            elif run_state.status == "cancelling":
                status = "cancelling, waiting for current turn"
            table.update_cell_at((row_index, 3), status)
            table.update_cell_at((row_index, 4), run_state.outcome or "")
        counts = {"failed": 0, "did_not_fail": 0, "running": 0, "pending": 0, "cancelled": 0}
        for run_state in self.state.runs.values():
            if run_state.status in {"running", "cancelling"}:
                counts["running"] += 1
            elif run_state.status == "pending":
                counts["pending"] += 1
            elif run_state.outcome in counts:
                counts[run_state.outcome] += 1
        self.query_one("#summary", Static).update(
            "Use ↑/↓ to select, r to run, a to run all, c to cancel, Enter to open completed runs"
            f" | {counts['failed']} failed, {counts['did_not_fail']} did_not_fail, {counts['running']} active, {counts['pending']} pending"
        )

    def action_run_selected(self) -> None:
        scenario_id = self._selected_scenario_id()
        if not scenario_id:
            return
        backend, agent = self._selected_backend_and_agent()
        token = threading.Event()
        self.state.cancel_tokens[scenario_id] = token
        self.state.ensure(scenario_id).status = "running"
        self._refresh_table()
        self.run_scenario(scenario_id, backend, agent, token)

    def action_run_all(self) -> None:
        backend, agent = self._selected_backend_and_agent()
        self.run_all_scenarios(backend, agent)

    def action_cancel_selected(self) -> None:
        scenario_id = self._selected_scenario_id()
        if not scenario_id:
            return
        token = self.state.cancel_tokens.get(scenario_id)
        run_state = self.state.runs.get(scenario_id)
        if token is None or run_state is None:
            return
        token.set()
        run_state.status = "cancelling"
        self._refresh_table()

    def action_open_selected(self) -> None:
        scenario_id = self._selected_scenario_id()
        if not scenario_id:
            return
        run_state = self.state.runs.get(scenario_id)
        if run_state is None or run_state.run_dir is None:
            return
        self.app.push_screen(ResultDetailScreen(run_state.run_dir))

    @work(thread=True)
    def run_scenario(self, scenario_id: str, backend: str, agent: str, token: threading.Event) -> None:
        result = run_scenario_worker(scenario_id, backend, agent, token)
        run_dir = result.run_dir
        if run_dir is None:
            return
        for event in tail_events(run_dir, stop=threading.Event(), poll_s=0.05):
            self.app.call_from_thread(self.post_message, RunEventMessage(event))

    @work(thread=True)
    def run_all_scenarios(self, backend: str, agent: str) -> None:
        for scenario_id in list_scenarios():
            token = threading.Event()
            self.state.cancel_tokens[scenario_id] = token
            self.state.ensure(scenario_id).status = "running"
            self.app.call_from_thread(self._refresh_table)
            result = run_scenario_worker(scenario_id, backend, agent, token)
            run_dir = result.run_dir
            if run_dir is None:
                continue
            for event in tail_events(run_dir, stop=threading.Event(), poll_s=0.05):
                self.app.call_from_thread(self.post_message, RunEventMessage(event))

    def on_run_event_message(self, message: RunEventMessage) -> None:
        apply_event(self.state, message.event)
        self._refresh_table()


class WebSafetyEvalApp(App):
    CSS = CSS

    def __init__(self, *, backend: str = "mock", agent: str = "") -> None:
        super().__init__()
        self.state = AppState(backend=backend, agent=agent)

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen(self.state))


def launch(*, backend: str = "mock", agent: str = "") -> None:
    WebSafetyEvalApp(backend=backend, agent=agent).run()
