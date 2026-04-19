from .runner import run_named_scenario

result = run_named_scenario("pi-body-text-001")
print(result.report_path)
