from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = ROOT / "scenarios"


def load_scenario(name: str) -> dict:
    scenario_dir = SCENARIOS_DIR / name
    with (scenario_dir / "scenario.json").open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["scenario_dir"] = scenario_dir
    return data
