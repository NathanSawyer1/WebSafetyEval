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


def validate_scenario(name: str, *, scenarios_dir: Path = SCENARIOS_DIR) -> list[str]:
    scenario_dir = scenarios_dir / name
    scenario_path = scenario_dir / "scenario.json"
    errors: list[str] = []

    if not scenario_path.exists():
        return [f"{name}: missing scenario.json"]

    try:
        raw = json.loads(scenario_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{name}: invalid JSON in scenario.json: {exc}"]

    raw["scenario_dir"] = scenario_dir
    try:
        scenario = ScenarioDef.model_validate(raw)
    except ValidationError as exc:
        return [f"{name}: invalid scenario schema: {exc}"]

    pages_dir = scenario_dir / "pages"
    if not pages_dir.exists():
        errors.append(f"{name}: missing pages/ directory")
        page_text = ""
    else:
        page_files = sorted(p for p in pages_dir.rglob("*") if p.is_file())
        page_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in page_files)

    entry_page = pages_dir / scenario.entry_page
    if not entry_page.exists():
        errors.append(f"{name}: entry_page not found: pages/{scenario.entry_page}")

    for idx, condition in enumerate(scenario.failure_conditions, start=1):
        if condition.url_contains and condition.url_contains not in page_text:
            errors.append(
                f"{name}: failure_conditions[{idx}].url_contains not found in pages: {condition.url_contains}"
            )

    return errors


def validate_all_scenarios(*, scenarios_dir: Path = SCENARIOS_DIR) -> dict[str, list[str]]:
    scenario_names = sorted(
        path.name
        for path in scenarios_dir.iterdir()
        if path.is_dir() and (path / "scenario.json").exists()
    )
    return {name: validate_scenario(name, scenarios_dir=scenarios_dir) for name in scenario_names}
