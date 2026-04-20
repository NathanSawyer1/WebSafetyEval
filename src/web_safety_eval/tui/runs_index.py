from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..__main__ import scenario_names
from ..scenario_loader import load_scenario


ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = ROOT / "runs"


def list_scenarios() -> list[str]:
    return scenario_names()


def load_scenario_meta(scenario_id: str) -> dict:
    scenario = load_scenario(scenario_id)
    return {
        "id": scenario["id"],
        "category": scenario.get("category", ""),
        "severity": scenario.get("severity_if_failed", ""),
    }


def read_run_artifacts(run_dir: Path) -> dict[str, Any]:
    report = (run_dir / "report.md").read_text(encoding="utf-8") if (run_dir / "report.md").exists() else ""
    tool_calls = json.loads((run_dir / "tool_calls.json").read_text(encoding="utf-8")) if (run_dir / "tool_calls.json").exists() else []
    transcript = json.loads((run_dir / "transcript.json").read_text(encoding="utf-8")) if (run_dir / "transcript.json").exists() else []
    return {
        "report": report,
        "tool_calls": tool_calls,
        "transcript": transcript,
        "run_dir": run_dir,
    }


def open_in_system(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    elif os.name == "nt":
        subprocess.run(["explorer.exe", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)
