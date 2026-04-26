from __future__ import annotations

import os
from pathlib import Path

from .mock_agent import MockAgent
from .openclaw_cli_agent import OpenClawCliAgent
from .openclaw_session_agent import OpenClawSessionAgent


def build_agent(run_dir: Path | None = None, entry_page: str | None = None):
    mode = os.environ.get("WEB_SAFETY_AGENT", "openclaw").strip().lower()
    if mode == "openclaw":
        return OpenClawCliAgent(entry_page=entry_page or "reviews.html")
    if mode == "openclaw_session":
        if run_dir is None:
            raise ValueError("run_dir is required for WEB_SAFETY_AGENT=openclaw_session")
        return OpenClawSessionAgent(run_dir=run_dir)
    if mode == "mock":
        if os.environ.get("WEB_SAFETY_DEV") != "1":
            raise ValueError("WEB_SAFETY_AGENT=mock requires WEB_SAFETY_DEV=1")
        return MockAgent(entry_page=entry_page or "reviews.html")
    raise ValueError(f"Unknown WEB_SAFETY_AGENT backend: {mode}")
