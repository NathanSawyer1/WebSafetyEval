from __future__ import annotations


import sys
from pathlib import Path
SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))

from web_safety_eval.runner import run_named_scenario

ROOT = Path(__file__).resolve().parent
SCENARIOS_DIR = ROOT / "scenarios"


def scenario_names() -> list[str]:
    return sorted(
        scenario_dir.name
        for scenario_dir in SCENARIOS_DIR.iterdir()
        if scenario_dir.is_dir() and (scenario_dir / "scenario.json").exists()
    )


def main() -> None:
    results = []
    for name in scenario_names():
        result = run_named_scenario(name)
        results.append(result)
        print(f"{name}: {result.outcome} ({result.report_path})")

    failed = sum(1 for result in results if result.outcome == "failed")
    did_not_fail = sum(1 for result in results if result.outcome == "did_not_fail")
    print()
    print(f"Summary: {failed} failed, {did_not_fail} did_not_fail, {len(results)} total")


if __name__ == "__main__":
    main()
