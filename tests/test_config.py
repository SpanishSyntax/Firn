"""Tests for Firn user configuration."""

from pathlib import Path
from firn.config import load_user_config


def test_load_user_config(tmp_path: Path, monkeypatch):
    cfg_file = tmp_path / "firn" / "firn.toml"
    cfg_file.parent.mkdir(parents=True)
    cfg_file.write_text('theme = "dark"\nport = 5000\n', encoding="utf-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    cfg = load_user_config()
    assert cfg.get("theme") == "dark"
    assert cfg.get("port") == 5000


def test_load_user_config_empty(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = load_user_config()
    assert cfg == {}
