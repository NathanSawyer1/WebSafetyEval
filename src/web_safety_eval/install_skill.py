from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

SKILL_NAME = "web-safety-eval"


@dataclass
class InstallResult:
    destination: Path
    files_written: list[Path]
    overwritten: bool


def default_openclaw_skill_dir() -> Path:
    """Resolve the default OpenClaw skills directory for the current user."""
    openclaw_home = os.environ.get("OPENCLAW_HOME")
    if openclaw_home:
        return Path(openclaw_home).expanduser() / "skills"
    return Path.home() / ".openclaw" / "skills"


def _skill_source_dir() -> Path:
    """Locate the packaged skill folder via importlib.resources.

    Works from a source checkout and from an installed wheel.
    """
    package_root = resources.files("web_safety_eval")
    skill_path = Path(str(package_root)) / "skills" / SKILL_NAME
    if not skill_path.exists():
        raise RuntimeError(
            f"Packaged skill not found at {skill_path}. "
            "This usually means the install is missing skill assets."
        )
    return skill_path


def _copy_tree(source: Path, destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for item in source.rglob("*"):
        if item.is_dir():
            continue
        relative = item.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item, target)
        written.append(target)
    return written


def install_skill(target: Path | None = None, *, force: bool = False) -> InstallResult:
    """Copy the packaged skill into the OpenClaw skills directory.

    target: destination parent (the skills dir). The skill lands at
      `<target>/web-safety-eval/`. If None, uses `default_openclaw_skill_dir()`.
    force: overwrite an existing skill folder.
    """
    source = _skill_source_dir()
    skills_dir = Path(target).expanduser() if target is not None else default_openclaw_skill_dir()
    destination = skills_dir / SKILL_NAME

    overwritten = destination.exists()
    if overwritten and not force:
        raise FileExistsError(
            f"Skill already installed at {destination}. Re-run with --force to overwrite."
        )
    if overwritten:
        shutil.rmtree(destination)

    files_written = _copy_tree(source, destination)
    return InstallResult(destination=destination, files_written=files_written, overwritten=overwritten)
