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
OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"


def list_scenarios() -> list[str]:
    return scenario_names()


def load_scenario_meta(scenario_id: str) -> dict:
    scenario = load_scenario(scenario_id)
    return {
        "id": scenario["id"],
        "category": scenario.get("category", ""),
        "severity": scenario.get("severity_if_failed", ""),
    }


def list_openclaw_agents() -> list[str]:
    if not OPENCLAW_CONFIG.exists():
        return []
    try:
        config = json.loads(OPENCLAW_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return []

    names: set[str] = set()
    agents = config.get("agents")
    if isinstance(agents, dict):
        names.update(str(name) for name in agents.keys())

    routing = config.get("routing")
    if isinstance(routing, dict):
        bindings = routing.get("bindings")
        if isinstance(bindings, dict):
            names.update(str(name) for name in bindings.keys())

    defaults = config.get("defaults")
    if isinstance(defaults, dict):
        agent_name = defaults.get("agent")
        if isinstance(agent_name, str) and agent_name.strip():
            names.add(agent_name.strip())

    return sorted(name for name in names if name)


def _format_tool_calls(tool_calls: list[dict[str, Any]]) -> str:
    if not tool_calls:
        return "No tool calls recorded."
    lines: list[str] = []
    for call in tool_calls:
        args_preview = json.dumps(call.get("args", {}), sort_keys=True)
        result_kind = (call.get("result") or {}).get("kind", "unknown")
        lines.append(
            f"step {call.get('step', '?')}: {call.get('tool', 'unknown')}"
            f"\n  args: {args_preview}"
            f"\n  result: {result_kind}"
        )
    return "\n\n".join(lines)


def _format_transcript(transcript: list[dict[str, Any]]) -> str:
    if not transcript:
        return "No transcript recorded."
    chunks: list[str] = []
    for idx, entry in enumerate(transcript, start=1):
        role = entry.get("role", "unknown")
        payload = json.dumps(entry.get("payload", {}), indent=2, sort_keys=True)
        chunks.append(f"[{idx}] {role}\n{payload}")
    return "\n\n".join(chunks)


def read_run_artifacts(run_dir: Path) -> dict[str, Any]:
    report = (run_dir / "report.md").read_text(encoding="utf-8") if (run_dir / "report.md").exists() else ""
    tool_calls = json.loads((run_dir / "tool_calls.json").read_text(encoding="utf-8")) if (run_dir / "tool_calls.json").exists() else []
    transcript = json.loads((run_dir / "transcript.json").read_text(encoding="utf-8")) if (run_dir / "transcript.json").exists() else []
    return {
        "report": report,
        "tool_calls": tool_calls,
        "tool_calls_text": _format_tool_calls(tool_calls),
        "transcript": transcript,
        "transcript_text": _format_transcript(transcript),
        "run_dir": run_dir,
    }


def open_in_system(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    elif os.name == "nt":
        subprocess.run(["explorer.exe", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)
