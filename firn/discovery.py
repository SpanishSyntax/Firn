"""Document discovery and search utilities for Firn."""

from __future__ import annotations

import sys
from pathlib import Path

from firn.ui import ui


def scan_recursive_markdown(root: Path) -> list[Path]:
    """Recursively discovers all Markdown documents excluding hidden dirs, node_modules, and git."""
    results: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".md", ".markdown", ".mdown"):
            parts = p.parts
            if any(
                part.startswith(".")
                or part in ("node_modules", "target", "result", "dist")
                for part in parts
            ):
                continue
            results.append(p)
    return sorted(results, key=lambda p: (len(p.parts), p.name.lower()))


def discover_markdown_target(raw_path: str | None = None, base_dir: Path | str = ".") -> Path:
    """Discovers a target Markdown document or interactively prompts if multiple/none."""
    search_dir = Path(base_dir).resolve()

    if raw_path:
        target = search_dir / raw_path if not Path(raw_path).is_absolute() else Path(raw_path)
        if target.is_file():
            return target
        elif target.is_dir():
            search_dir = target
        else:
            ui.error(f"File '{raw_path}' not found.")
            sys.exit(1)

    md_files = sorted(
        [
            p
            for p in search_dir.iterdir()
            if p.is_file() and p.suffix.lower() in (".md", ".markdown", ".mdown")
        ],
        key=lambda p: (0 if p.name.lower() == "readme.md" else 1, p.name.lower()),
    )

    if not md_files:
        if sys.stdin.isatty():
            lines = [
                f"{ui.bold('Active Directory:')} {search_dir}",
                f"{ui.bold('Target Document:')}  {ui.dim('No markdown documents (*.md) found in current directory')}",
            ]
            ui.panel("FIRN GFM DOCUMENT VIEWER", lines)
            action = ui.select(
                f"No Markdown document found in '{search_dir.name}'. What would you like to do?",
                [
                    ("scan", "Search subdirectories recursively for *.md files"),
                    ("help", "Show help and command usage"),
                    ("exit", "Exit"),
                ],
            )
            if action == "scan":
                nested = scan_recursive_markdown(search_dir)
                if not nested:
                    ui.error(f"No Markdown files found under '{search_dir}'.")
                    sys.exit(1)
                options = [
                    (
                        str(f),
                        f"📄 {f.relative_to(search_dir)}",
                        f"{f.stat().st_size:,} bytes",
                    )
                    for f in nested
                ]
                chosen = ui.select("Select a Markdown document to open:", options)
                return Path(chosen).resolve()
            else:
                sys.exit(0)

        ui.error(f"No Markdown files found in '{search_dir}'. Specify one: firn <file.md>")
        sys.exit(1)

    if len(md_files) == 1:
        return md_files[0].resolve()

    if sys.stdin.isatty():
        options = [
            (str(f.resolve()), f"📄 {f.name}", f"{f.stat().st_size:,} bytes")
            for f in md_files
        ]
        chosen = ui.select(
            "Multiple Markdown documents found. Select one to open:", options
        )
        return Path(chosen).resolve()

    return md_files[0].resolve()
