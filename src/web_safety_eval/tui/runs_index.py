from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from ..__main__ import scenario_names
from ..scenario_loader import load_scenario


def list_scenarios() -> list[str]:
    return scenario_names()


def load_scenario_meta(scenario_id: str) -> dict:
    scenario = load_scenario(scenario_id)
    return {
        'id': scenario['id'],
        'category': scenario.get('category', ''),
        'severity': scenario.get('severity_if_failed', ''),
    }


def open_in_system(path: Path) -> None:
    if sys.platform == 'darwin':
        subprocess.run(['open', str(path)], check=False)
    elif os.name == 'nt':
        subprocess.run(['explorer.exe', str(path)], check=False)
    else:
        subprocess.run(['xdg-open', str(path)], check=False)
