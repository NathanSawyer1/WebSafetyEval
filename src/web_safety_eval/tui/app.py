from __future__ import annotations

import threading
from typing import Iterable

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Select, Static
from textual import work

from .events import RunEvent
from .messages import RunEventMessage
from .runs_index import list_scenarios, load_scenario_meta
from .state import AppState, apply_event
from .tail import tail_events
from .worker import run_scenario_worker

CSS = """
Screen { layout: vertical; }
#controls { height: 3; }
#summary { height: 1; }
DataTable { height: 1fr; }
"""


class DashboardScreen(Screen):
    BINDINGS = [Binding('r', 'run_selected', 'Run selected'), Binding('q', 'quit', 'Quit')]

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self._watch_stops: dict[str, threading.Event] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id='controls'):
            yield Select([(value, value) for value in ['mock', 'openclaw', 'openclaw_session']], value=self.state.backend, id='backend')
            yield Input(value=self.state.agent, placeholder='agent', id='agent')
        yield DataTable(id='scenarios')
        yield Static('', id='summary')
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one('#scenarios', DataTable)
        table.add_columns('id', 'category', 'severity', 'status', 'outcome')
        for scenario_id in list_scenarios():
            meta = load_scenario_meta(scenario_id)
            self.state.ensure(scenario_id)
            table.add_row(meta['id'], meta['category'], meta['severity'], 'pending', '', key=scenario_id)
        self._refresh_table()

    def _refresh_table(self) -> None:
        table = self.query_one('#scenarios', DataTable)
        for scenario_id, run_state in self.state.runs.items():
            try:
                row_index = table.get_row_index(scenario_id)
            except Exception:
                continue
            status = run_state.status
            if run_state.status == 'running' and run_state.last_tool:
                status = f'running step {run_state.current_step} {run_state.last_tool}'
            table.update_cell_at((row_index, 3), status)
            table.update_cell_at((row_index, 4), run_state.outcome or '')
        counts = {'failed': 0, 'did_not_fail': 0, 'running': 0, 'pending': 0, 'cancelled': 0}
        for run_state in self.state.runs.values():
            if run_state.status == 'running':
                counts['running'] += 1
            elif run_state.status == 'pending':
                counts['pending'] += 1
            elif run_state.outcome in counts:
                counts[run_state.outcome] += 1
        self.query_one('#summary', Static).update(
            f"{counts['failed']} failed, {counts['did_not_fail']} did_not_fail, {counts['running']} running, {counts['pending']} pending"
        )

    def action_run_selected(self) -> None:
        table = self.query_one('#scenarios', DataTable)
        if table.cursor_row is None:
            return
        scenario_id = str(table.get_row_at(table.cursor_row)[0])
        backend = str(self.query_one('#backend', Select).value)
        agent = self.query_one('#agent', Input).value
        self.state.backend = backend
        self.state.agent = agent
        token = threading.Event()
        self.state.cancel_tokens[scenario_id] = token
        self.run_scenario(scenario_id, backend, agent, token)

    @work(thread=True)
    def run_scenario(self, scenario_id: str, backend: str, agent: str, token: threading.Event) -> None:
        result = run_scenario_worker(scenario_id, backend, agent, token)
        stop = threading.Event()
        run_dir = result.run_dir
        if run_dir is None:
            return
        for event in tail_events(run_dir, stop=stop, poll_s=0.05):
            self.app.call_from_thread(self.post_message, RunEventMessage(event))

    def on_run_event_message(self, message: RunEventMessage) -> None:
        apply_event(self.state, message.event)
        self._refresh_table()


class WebSafetyEvalApp(App):
    CSS = CSS

    def __init__(self, *, backend: str = 'mock', agent: str = '') -> None:
        super().__init__()
        self.state = AppState(backend=backend, agent=agent)

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen(self.state))


def launch(*, backend: str = 'mock', agent: str = '') -> None:
    WebSafetyEvalApp(backend=backend, agent=agent).run()
