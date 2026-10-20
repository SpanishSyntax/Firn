"""Tests for Firn core process primitives and configuration."""

from pathlib import Path
from firn.core import find_ephemeral_port, resolve_github_token, RenderConfig


def test_find_ephemeral_port():
    port = find_ephemeral_port("127.0.0.1")
    assert isinstance(port, int)
    assert 1024 <= port <= 65535


def test_resolve_github_token_explicit():
    token, source = resolve_github_token(explicit_token="ghp_test123")
    assert token == "ghp_test123"
    assert "token" in source.lower()


def test_resolve_github_token_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_envtoken")
    token, source = resolve_github_token()
    assert token == "ghp_envtoken"
    assert "github_token" in source.lower()


def test_render_config():
    cfg = RenderConfig(target_path=Path("README.md"), width=1200, height=900)
    assert cfg.width == 1200
    assert cfg.height == 900
    assert cfg.target_path == Path("README.md")
