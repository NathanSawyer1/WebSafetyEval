from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .models import ScenarioDef

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = ROOT / "scenarios"


def load_scenario(name: str) -> dict:
    scenario_dir = SCENARIOS_DIR / name
    with (scenario_dir / "scenario.json").open("r", encoding="utf-8") as f:
        raw = json.load(f)
    raw["scenario_dir"] = scenario_dir
    try:
        scenario = ScenarioDef.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid scenario '{name}': {exc}") from exc
    return scenario.model_dump(mode="python")
