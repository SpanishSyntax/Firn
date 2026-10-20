"""Entrypoint and CLI argument parser for Firn."""

import argparse
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from firn import __version__
from firn.core import GripOrchestrator, GripStartupError, RenderConfig
from firn.ui import ui
from firn.viewer import launch_viewer


def print_help():
    """Prints beautiful colored usage instructions matching Folio, Glaze, & Flaker."""
    app = ui.app_name
    print(f"""{ui.badge()} {ui.bold("Instant GitHub-Flavored Markdown (GFM) Native Desktop Viewer")}

{ui.blue("Usage:")}
  {app} <path-to-markdown> [options]
  {app} [directory] [options]            Auto-discover README.md or select *.md interactively

{ui.blue("Options:")}
  -p, --port PORT        Bind specific localhost port (default: random ephemeral port)
  --host HOST            Bind address for grip daemon (default: 127.0.0.1)
  -g, --github-mode      Render with GitHub repository Box chrome & page layout
  -w, --wide             Render wide GitHub document container (--wide)
  -u, --user-content     Render as GitHub user-content (issues/comments mode)
  -c, --context REPO     Repository context (e.g. SpanishSyntax/Firn) for autolinks
  -t, --title TITLE      Override window title (default: "Firn: <filename>")
  --theme MODE           Viewer color theme: auto, dark, light (default: auto)
  --dark / --light       Shortcut for --theme=dark / --theme=light
  --frameless            Launch in a frameless minimal native window
  --width PX             Initial window width in pixels (default: 980)
  --height PX            Initial window height in pixels (default: 860)
  --token TOKEN          Explicit GitHub Personal Access Token (or set GITHUB_TOKEN)
  --pass-path ENTRY      Password-store (`pass`) entry for GitHub token
  --api-url URL          Custom GitHub API base URL
  --inline               Inline CSS styles instead of passing --no-inline to grip
  --clear-cache          Clear cached GitHub CSS assets via `grip --clear` and exit
  --debug                Enable WebKit inspector / developer tools in viewer window
  --color MODE           Color output mode: auto, always, never (default: auto)
  --no-color             Disable colored terminal output
  -h, --help             Show this help message and exit
  -V, -v, --version      Show version information and exit

{ui.blue("Examples:")}
  {app} README.md                      # Open README.md in native WebKitGTK window
  {app} README.md -g                   # Open with full GitHub repository Box layout
  {app} docs/architecture.md --dark    # Render in GitHub Dark mode
  {app} SPEC.md --frameless --wide     # Frameless wide native window
  {app} .                              # Auto-discover or pick Markdown file in current dir
""")


def handle_color_args():
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--no-color":
            ui.set_color_mode("never")
        elif arg.startswith("--color="):
            ui.set_color_mode(arg.split("=", 1)[1])
        elif arg == "--color" and i + 1 < len(sys.argv[1:]):
            ui.set_color_mode(sys.argv[1:][i + 1])


def load_user_config() -> dict[str, Any]:
    """Loads optional user defaults from ~/.config/firn/firn.toml."""
    xdg_cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    cfg_path = xdg_cfg / "firn" / "firn.toml"
    if not cfg_path.is_file():
        return {}
    try:
        data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
        if isinstance(data.get("general"), dict):
            merged = dict(data)
            general = merged.pop("general")
            return {**general, **merged}
        return data
    except Exception as exc:
        ui.warn(f"Failed to parse {cfg_path}: {exc}")
        return {}


def clear_grip_cache() -> int:
    grip_bin = shutil.which("grip")
    if not grip_bin:
        ui.error("Could not find 'grip' executable in PATH.")
        return 1
    with ui.spinner("Clearing cached GitHub CSS assets..."):
        res = subprocess.run([grip_bin, "--clear"], capture_output=True, text=True)
    if res.returncode == 0:
        ui.success("Cleared cached GitHub styles and assets.")
        return 0
    ui.error_panel("Failed to Clear Cache", res.stderr.strip() or "Unknown grip error.")
    return res.returncode


def _scan_recursive_markdown(root: Path) -> list[Path]:
    """Finds Markdown files across subdirectories (excluding hidden and build dirs)."""
    excluded = {".git", ".direnv", "node_modules", "__pycache__", "build", "dist", "result"}
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [
            d for d in dirnames if d not in excluded and not d.startswith(".")
        ]
        dp = Path(dirpath)
        for fn in filenames:
            if fn.startswith("."):
                continue
            p = dp / fn
            if p.suffix.lower() in (".md", ".markdown", ".mdown"):
                found.append(p.resolve())
    found.sort(key=lambda p: (0 if p.name.lower() == "readme.md" else 1, str(p).lower()))
    return found


def discover_markdown_target(raw_path: str | None) -> Path:
    """Resolves a target Markdown path or offers an interactive picker matching Folio."""
    if raw_path:
        candidate = Path(raw_path).expanduser()
        if candidate.is_file():
            return candidate.resolve()
        if candidate.is_dir():
            search_dir = candidate.resolve()
        else:
            ui.error(f"File '{raw_path}' not found.")
            sys.exit(1)
    else:
        search_dir = Path.cwd()

    md_files = sorted(
        [
            p
            for p in search_dir.iterdir()
            if p.is_file() and p.suffix.lower() in (".md", ".markdown", ".mdown")
        ],
        key=lambda p: (0 if p.name.lower() == "readme.md" else 1, p.name.lower()),
    )

    if not md_files:
        lines = [
            f"{ui.bold('Firn Version:')}     {ui.bold_cyan(f'v{__version__}')} (Engine: Grip / GFM Desktop Viewer)",
            f"{ui.bold('Active Directory:')} {search_dir}",
            f"{ui.bold('Target Document:')}  {ui.dim('No markdown documents (*.md) found in current directory')}",
        ]
        ui.panel("FIRN GFM DOCUMENT VIEWER", lines)

        if sys.stdin.isatty():
            action = ui.select(
                f"No Markdown document found in '{search_dir.name}'. What would you like to do?",
                [
                    ("scan", "Search subdirectories recursively for *.md files"),
                    ("help", "Show help and command usage"),
                    ("clear", "Clear cached GitHub CSS assets (grip --clear)"),
                    ("exit", "Exit"),
                ],
            )
            if action == "scan":
                nested = _scan_recursive_markdown(search_dir)
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
            elif action == "help":
                print_help()
                sys.exit(0)
            elif action == "clear":
                sys.exit(clear_grip_cache())
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


def main():
    handle_color_args()
    raw_args = sys.argv[1:]

    if any(a in ("-h", "--help", "help") for a in raw_args):
        print_help()
        sys.exit(0)

    if any(a in ("-V", "-v", "--version", "version") for a in raw_args):
        print(f"{ui.badge()} {ui.bold(f'v{__version__}')}")
        sys.exit(0)

    user_cfg = load_user_config()

    parser = argparse.ArgumentParser(prog="firn", add_help=False)
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Path to the Markdown document (or directory) to preview.",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=int(user_cfg.get("port", 0)),
        help="Local port to bind (0 = ephemeral).",
    )
    parser.add_argument(
        "--host",
        default=str(user_cfg.get("host", "127.0.0.1")),
        help="Local loopback address to bind.",
    )
    parser.add_argument(
        "-g",
        "--github-mode",
        "--github",
        dest="github_mode",
        action="store_true",
        default=bool(user_cfg.get("github_mode", False)),
        help="Render with GitHub repository Box chrome & page layout.",
    )
    parser.add_argument(
        "-w",
        "--wide",
        action="store_true",
        default=bool(user_cfg.get("wide", False)),
        help="Render wide GitHub container.",
    )
    parser.add_argument(
        "-u",
        "--user-content",
        action="store_true",
        default=bool(user_cfg.get("user_content", False)),
        help="Render as GitHub user-content (comments/issues).",
    )
    parser.add_argument(
        "-c",
        "--context",
        default=user_cfg.get("context"),
        help="Repository context (owner/repo).",
    )
    parser.add_argument(
        "-t",
        "--title",
        default=user_cfg.get("title"),
        help="Custom window and document title.",
    )
    parser.add_argument(
        "--theme",
        choices=["auto", "dark", "light"],
        default=str(user_cfg.get("theme", "auto")),
        help="Color theme mode (auto, dark, light).",
    )
    parser.add_argument(
        "--dark",
        dest="theme",
        action="store_const",
        const="dark",
        help="Shortcut for --theme=dark.",
    )
    parser.add_argument(
        "--light",
        dest="theme",
        action="store_const",
        const="light",
        help="Shortcut for --theme=light.",
    )
    parser.add_argument(
        "--frameless",
        action="store_true",
        default=bool(user_cfg.get("frameless", False)),
        help="Launch pywebview in a frameless minimal desktop window.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=int(user_cfg.get("width", 980)),
        help="Window width in pixels.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=int(user_cfg.get("height", 860)),
        help="Window height in pixels.",
    )
    parser.add_argument("--token", default=user_cfg.get("token"), help="GitHub Personal Access Token.")
    parser.add_argument(
        "--pass-path",
        default=user_cfg.get("pass_path"),
        help="Password-store entry path for GitHub token.",
    )
    parser.add_argument(
        "--api-url",
        default=user_cfg.get("api_url"),
        help="Custom GitHub API base URL.",
    )
    parser.add_argument(
        "--inline",
        dest="no_inline",
        action="store_false",
        default=bool(user_cfg.get("no_inline", True)),
        help="Inline styles instead of passing --no-inline to grip.",
    )
    parser.add_argument(
        "--no-inline",
        dest="no_inline",
        action="store_true",
        help="Pass --no-inline to grip (default).",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear grip cached styles and exit.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=bool(user_cfg.get("debug", False)),
        help="Enable WebKit debug inspector.",
    )
    parser.add_argument("--color", choices=["auto", "always", "never"], default="auto")
    parser.add_argument("--no-color", action="store_true")

    args = parser.parse_args()

    if args.clear_cache:
        sys.exit(clear_grip_cache())

    target_md = discover_markdown_target(args.path)

    mode_str = "GitHub Box" if args.github_mode else "GFM Standard"
    theme_str = args.theme.capitalize()
    frame_str = "Frameless" if args.frameless else f"{args.width}x{args.height}"
    lines = [
        f"{ui.bold('Target Document:')}  {ui.cyan(str(target_md))} ({target_md.stat().st_size:,} bytes)",
        f"{ui.bold('Viewer Mode:')}      {ui.green(mode_str)} | Theme: {ui.magenta(theme_str)} | Window: {frame_str}",
        f"{ui.bold('Rendering Engine:')} Grip (Local WebKit / PyWebView runtime)",
    ]
    ui.panel("FIRN GFM DOCUMENT VIEWER", lines)

    config = RenderConfig(
        target_path=target_md,
        host=args.host,
        port=args.port,
        wide=args.wide,
        user_content=args.user_content,
        context=args.context,
        title=args.title,
        api_url=args.api_url,
        token=args.token,
        pass_path=args.pass_path,
        no_inline=args.no_inline,
        frameless=args.frameless,
        github_mode=args.github_mode,
        theme=args.theme,
        width=args.width,
        height=args.height,
        debug=args.debug,
    )

    orchestrator = GripOrchestrator(config)
    try:
        orchestrator.start()
        launch_viewer(orchestrator, config)
    except GripStartupError as exc:
        ui.error_panel(
            "Grip Engine Failed to Start",
            [
                *str(exc).splitlines(),
                "",
                "Tip: Set GITHUB_TOKEN or store a token in `pass` (github/token) to avoid rate limits.",
            ],
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        orchestrator.stop()
        sys.exit(0)
    except Exception as exc:
        orchestrator.stop()
        ui.error_panel("Viewer Runtime Error", str(exc).splitlines())
        sys.exit(1)


if __name__ == "__main__":
    main()
