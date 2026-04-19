import os

from web_safety_eval.runner import run_named_scenario

if __name__ == "__main__":
    scenario_name = os.environ.get("WEB_SAFETY_SCENARIO", "pi-body-text-001")
    result = run_named_scenario(scenario_name)
    print(f"Run complete: {result.run_dir}")
    print(f"Outcome: {result.outcome}")
    print(f"Report: {result.report_path}")
