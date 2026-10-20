"""Tests for Firn CLI argument parsing and flags."""

from firn import __version__
from firn.cli import main


def test_cli_version(capsys):
    ret = main(["--version"])
    assert ret == 0
    captured = capsys.readouterr()
    assert f"v{__version__}" in captured.out


def test_cli_help(capsys):
    ret = main(["--help"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Instant GitHub-Flavored Markdown" in captured.out
