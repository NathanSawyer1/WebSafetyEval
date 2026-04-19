from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

from tests.mocks.openclaw_http_server import MockOpenClawHttpServer


REPO = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = REPO / "scenarios"


def _scenario_names() -> list[str]:
    return sorted(
        scenario_dir.name
        for scenario_dir in SCENARIOS_DIR.iterdir()
        if scenario_dir.is_dir()
        and (scenario_dir / "scenario.json").exists()
        and (scenario_dir / "pages" / "reviews.html").exists()
    )


@pytest.mark.parametrize("scenario", _scenario_names())
def test_openclaw_http_wrapper_runs_against_mock_server(tmp_path: Path, scenario: str):
    server = MockOpenClawHttpServer()
    server.start()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        env["OPENCLAW_HTTP_URL"] = server.base_url
        env["WEB_SAFETY_SCENARIO"] = scenario
        proc = subprocess.run(
            [sys.executable, "run_openclaw_http_demo.py"],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert "Run complete:" in proc.stdout
        assert "Outcome:" in proc.stdout
        assert "Report:" in proc.stdout

        run_dir = _extract_run_dir(proc.stdout)
        assert run_dir.exists()
        assert (run_dir / "result.json").exists()
        assert (run_dir / "transcript.json").exists()
        assert (run_dir / "tool_calls.json").exists()
        assert (run_dir / "report.md").exists()

        agent_io_dir = run_dir / "agent_io"
        assert agent_io_dir.exists()
        request_files = sorted(agent_io_dir.glob("request-*.json"))
        response_files = sorted(agent_io_dir.glob("response-*.json"))
        assert request_files
        assert response_files
        assert len(response_files) == len(request_files)
        assert (agent_io_dir / "done.json").exists()

        step_requests = [req for req in server.requests if req["method"] == "POST" and req["path"].endswith("/step")]
        assert step_requests, server.requests
        assert any(req["body"].get("phase") == "start" for req in step_requests), step_requests

        tool_calls = json.loads((run_dir / "tool_calls.json").read_text(encoding="utf-8"))
        assert all(call["tool"] == "browser.fetch" for call in tool_calls)
    finally:
        server.stop()


def test_mock_openclaw_http_server_lifecycle():
    server = MockOpenClawHttpServer()
    server.start()
    try:
        parsed = urlparse(server.base_url)
        assert parsed.scheme == "http"
        assert parsed.hostname == "127.0.0.1"
        assert parsed.port is not None and parsed.port > 0
    finally:
        server.stop()


def _extract_run_dir(stdout: str) -> Path:
    prefix = "Run complete: "
    for line in stdout.splitlines():
        if line.startswith(prefix):
            return Path(line[len(prefix):].strip())
    raise AssertionError(f"Could not find run directory in stdout:\n{stdout}")
