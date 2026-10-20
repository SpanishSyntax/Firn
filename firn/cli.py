"""CLI router, argument parser, and desktop application launcher for Firn."""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Any, Sequence

from firn import __version__
from firn.config import load_user_config
from firn.core import (
    GripOrchestrator,
    GripStartupError,
    RenderConfig,
    find_ephemeral_port,
    resolve_github_token,
)
from firn.discovery import discover_markdown_target, scan_recursive_markdown
from firn.ui import add_color_args, handle_color_args, ui
from firn.viewer import launch_viewer

__all__ = [
    "main",
    "discover_markdown_target",
    "scan_recursive_markdown",
    "clear_grip_cache",
    "load_user_config",
    "find_ephemeral_port",
    "resolve_github_token",
    "RenderConfig",
    "GripOrchestrator",
    "launch_viewer",
]


def clear_grip_cache() -> int:
    """Invokes grip to clear locally cached GitHub styling assets."""
    with ui.spinner("Clearing local grip cached assets...") as sp:
        try:
            res = subprocess.run(
                ["grip", "--clear"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                sp.stop("Successfully cleared grip cached styles.", ok=True)
                return 0
            else:
                sp.stop("Failed to clear grip cache.", ok=False)
                ui.error_panel(
                    "Failed to Clear Cache",
                    res.stderr.strip() or "Unknown grip error.",
                )
                return 1
        except Exception as exc:
            sp.stop("Error executing grip.", ok=False)
            ui.error(f"Cannot run grip: {exc}")
            return 1


def print_help() -> None:
    """Prints colored usage instructions matching Flaker, Glaze, Folio, and Borealis."""
    print(f"""{ui.badge()} {ui.bold("Instant GitHub-Flavored Markdown (GFM) Native Desktop Viewer")}

{ui.blue("Usage:")}
  firn <path-to-markdown> [options]
  firn [directory] [options]            Auto-discover README.md or select *.md interactively

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
  firn README.md                      # Open README.md in native WebKitGTK window
  firn README.md -g                   # Open with full GitHub repository Box layout
  firn docs/architecture.md --dark    # Render in GitHub Dark mode
  firn SPEC.md --frameless --wide     # Frameless wide native window
  firn .                              # Auto-discover or pick Markdown file in current dir
""")


def _build_parser(user_cfg: dict[str, Any]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="firn", add_help=False)
    parser.add_argument("path", nargs="?", default=None, help="Path to Markdown document to preview.")
    parser.add_argument("-p", "--port", type=int, default=int(user_cfg.get("port", 0)), help="Local port.")
    parser.add_argument("--host", default=str(user_cfg.get("host", "127.0.0.1")), help="Local host.")
    parser.add_argument("-g", "--github-mode", "--github", dest="github_mode", action="store_true", default=bool(user_cfg.get("github_mode", False)))
    parser.add_argument("-w", "--wide", action="store_true", default=bool(user_cfg.get("wide", False)))
    parser.add_argument("-u", "--user-content", action="store_true", default=bool(user_cfg.get("user_content", False)))
    parser.add_argument("-c", "--context", default=user_cfg.get("context"))
    parser.add_argument("-t", "--title", default=user_cfg.get("title"))
    parser.add_argument("--theme", choices=["auto", "dark", "light"], default=str(user_cfg.get("theme", "auto")))
    parser.add_argument("--dark", dest="theme", action="store_const", const="dark")
    parser.add_argument("--light", dest="theme", action="store_const", const="light")
    parser.add_argument("--frameless", action="store_true", default=bool(user_cfg.get("frameless", False)))
    parser.add_argument("--width", type=int, default=int(user_cfg.get("width", 980)))
    parser.add_argument("--height", type=int, default=int(user_cfg.get("height", 860)))
    parser.add_argument("--token", default=user_cfg.get("token"))
    parser.add_argument("--pass-path", default=user_cfg.get("pass_path"))
    parser.add_argument("--api-url", default=user_cfg.get("api_url"))
    parser.add_argument("--inline", dest="no_inline", action="store_false", default=bool(user_cfg.get("no_inline", True)))
    parser.add_argument("--no-inline", dest="no_inline", action="store_true")
    parser.add_argument("--clear-cache", action="store_true")
    parser.add_argument("--debug", action="store_true", default=bool(user_cfg.get("debug", False)))
    add_color_args(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    handle_color_args(raw_args)

    if any(a in ("-h", "--help", "help") for a in raw_args):
        print_help()
        return 0

    if any(a in ("-V", "-v", "--version", "version") for a in raw_args):
        print(f"{ui.badge()} {ui.bold(f'v{__version__}')}")
        return 0

    user_cfg = load_user_config()
    parser = _build_parser(user_cfg)
    args = parser.parse_args(raw_args)

    if args.clear_cache:
        return clear_grip_cache()

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
        return 1
    except KeyboardInterrupt:
        print()
        orchestrator.stop()
        return 0
    except Exception as exc:
        orchestrator.stop()
        ui.error_panel("Viewer Runtime Error", str(exc).splitlines())
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
