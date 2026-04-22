from __future__ import annotations

from pathlib import Path

import pytest

from web_safety_eval.install_skill import default_skill_target, install_skill


def test_default_skill_target_uses_openclaw_home(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path / "custom-openclaw"))
    assert default_skill_target() == tmp_path / "custom-openclaw" / "skills" / "web-safety-eval"


def test_install_skill_copies_packaged_skill(tmp_path):
    destination = tmp_path / "skills" / "web-safety-eval"
    installed = install_skill(target=str(destination))
    assert installed == destination
    skill = destination / "SKILL.md"
    assert skill.exists()
    assert "web safety eval" in skill.read_text().lower()


def test_install_skill_refuses_to_overwrite_without_force(tmp_path):
    destination = tmp_path / "skills" / "web-safety-eval"
    destination.mkdir(parents=True)
    (destination / "SKILL.md").write_text("old")

    with pytest.raises(FileExistsError):
        install_skill(target=str(destination))


def test_install_skill_force_overwrites_existing_install(tmp_path):
    destination = tmp_path / "skills" / "web-safety-eval"
    destination.mkdir(parents=True)
    (destination / "SKILL.md").write_text("old")

    install_skill(target=str(destination), force=True)

    assert "web safety eval" in (destination / "SKILL.md").read_text().lower()
