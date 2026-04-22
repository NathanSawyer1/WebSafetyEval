from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

import pytest

from web_safety_eval import __main__ as cli
from web_safety_eval.install_skill import (
    default_openclaw_skill_dir,
    install_skill,
)


def test_default_skill_dir_uses_openclaw_home(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
    assert default_openclaw_skill_dir() == tmp_path / "skills"


def test_default_skill_dir_falls_back_to_home(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENCLAW_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert default_openclaw_skill_dir() == tmp_path / ".openclaw" / "skills"


def test_install_skill_copies_skill_md(tmp_path):
    result = install_skill(target=tmp_path)
    installed = tmp_path / "web-safety-eval" / "SKILL.md"
    assert installed.exists()
    assert result.destination == tmp_path / "web-safety-eval"
    assert installed in result.files_written
    body = installed.read_text(encoding="utf-8")
    assert "web-safety-eval" in body
    assert "OpenClaw" in body


def test_install_skill_refuses_overwrite_without_force(tmp_path):
    install_skill(target=tmp_path)
    with pytest.raises(FileExistsError):
        install_skill(target=tmp_path)


def test_install_skill_force_overwrites(tmp_path):
    install_skill(target=tmp_path)
    installed = tmp_path / "web-safety-eval" / "SKILL.md"
    installed.write_text("tampered", encoding="utf-8")
    result = install_skill(target=tmp_path, force=True)
    assert result.overwritten is True
    assert installed.read_text(encoding="utf-8") != "tampered"
    assert "web-safety-eval" in installed.read_text(encoding="utf-8")


def test_cli_install_skill_succeeds(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys,
        "argv",
        ["web-safety-eval", "install-skill", "--target", str(tmp_path)],
    )
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cli.main()
    output = buf.getvalue()
    assert "Installed skill at" in output
    assert (tmp_path / "web-safety-eval" / "SKILL.md").exists()


def test_cli_install_skill_exits_when_exists_without_force(monkeypatch, tmp_path):
    install_skill(target=tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["web-safety-eval", "install-skill", "--target", str(tmp_path)],
    )
    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == 2
    assert "--force" in buf.getvalue()
