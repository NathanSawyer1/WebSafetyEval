from __future__ import annotations

import os
import shutil
from importlib import resources
from pathlib import Path

SKILL_NAME = "web-safety-eval"


def default_skill_target() -> Path:
    openclaw_home = os.environ.get("OPENCLAW_HOME")
    base = Path(openclaw_home).expanduser() if openclaw_home else Path.home() / ".openclaw"
    return base / "skills" / SKILL_NAME


def install_skill(*, target: str | None = None, force: bool = False) -> Path:
    destination = Path(target).expanduser() if target else default_skill_target()
    source = resources.files("web_safety_eval").joinpath("skills", SKILL_NAME)

    if destination.exists():
        if not force:
            raise FileExistsError(f"Refusing to overwrite existing skill install: {destination}")
        shutil.rmtree(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(Path(source), destination)
    return destination
