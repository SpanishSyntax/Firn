"""Tests for Firn document discovery and recursive search."""

from pathlib import Path
from firn.discovery import discover_markdown_target, scan_recursive_markdown


def test_discover_markdown_target_explicit(tmp_path: Path):
    doc = tmp_path / "custom.md"
    doc.write_text("# Custom", encoding="utf-8")
    found = discover_markdown_target(str(doc), base_dir=tmp_path)
    assert found == doc


def test_discover_markdown_target_readme_priority(tmp_path: Path):
    (tmp_path / "other.md").write_text("# Other", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Readme", encoding="utf-8")
    found = discover_markdown_target(None, base_dir=tmp_path)
    assert found.name == "README.md"


def test_scan_recursive_markdown(tmp_path: Path):
    (tmp_path / "doc1.md").write_text("1", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "doc2.markdown").write_text("2", encoding="utf-8")
    node_mod = tmp_path / "node_modules"
    node_mod.mkdir()
    (node_mod / "ignored.md").write_text("3", encoding="utf-8")

    results = scan_recursive_markdown(tmp_path)
    names = [r.name for r in results]
    assert "doc1.md" in names
    assert "doc2.markdown" in names
    assert "ignored.md" not in names
