# Firn 🧊

> **Instant GitHub-Flavored Markdown (GFM) Native Desktop Document Viewer**

Firn is a dedicated, zero-clutter native desktop viewer for GitHub-Flavored Markdown (GFM) built for the **Frost** ecosystem alongside `Flaker`, `Borealis`, `Glaze`, and `Folio`. It pairs [`grip`](https://github.com/joeyespo/grip) (which renders via GitHub's official Markdown API and Primer CSS) with an ephemeral local `pywebview` / WebKit2GTK window that automatically terminates the background server the instant the window closes.

---

## ✨ Features

- 🐙 **100% GitHub Rendering Parity**:
  - **GitHub Alerts / Callouts**: Native rendering for `[!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, and `[!CAUTION]`.
  - **Diagrams & Flowcharts**: Automatic client-side **Mermaid.js** diagram rendering for ```` ```mermaid ```` blocks.
  - **Mathematical Typesetting**: Inline (`$...$`) and display (`$$...$$`) LaTeX math powered by **KaTeX**.
  - **GFM Tables, Task Lists & Syntax Highlighting**: Exact GitHub Primer typography and code highlighting.
- 🪟 **Isolated Native Desktop Frame**: Renders inside a lightweight `pywebview` (GTK3 / WebKit2GTK) window on Wayland and X11—no browser tab clutter or lingering background dev servers.
- 🔌 **Ephemeral Loopback & Strict Teardown**: Dynamically binds a random unprivileged localhost port, spawns `grip --no-inline` in an isolated process group with Linux `PR_SET_PDEATHSIG`, and guarantees immediate daemon teardown on window exit or signal (`SIGINT`, `SIGTERM`, `SIGHUP`).
- 🔐 **Zero-Config Token Discovery**: Seamlessly bypasses GitHub's 60 req/hr anonymous rate limit (unlocking 5,000 req/hr) by checking `GITHUB_TOKEN` / `GRIP_TOKEN` / `GH_TOKEN`, `~/.config/firn/token`, standard `pass` (`password-store`) paths (`github/token`, `github/pat`), or `gh auth token`.
- 🌗 **Adaptive Dark & Light Modes**: Follows system color scheme (`--theme auto`), forces GitHub Dark (`--dark`) or Light (`--light`), or toggles live with `t`.

---

## 🚀 Quick Start

Run Firn directly via Nix without installing:

```bash
# Render README.md in an isolated native desktop window
nix run github:SpanishSyntax/Firn -- README.md

# Force GitHub Dark mode in a wide layout
nix run github:SpanishSyntax/Firn -- README.md --dark --wide

# Launch in a minimal frameless window
nix run github:SpanishSyntax/Firn -- docs/spec.md --frameless

# Auto-discover or interactively pick a Markdown file in the current directory
nix run github:SpanishSyntax/Firn
```

---

## 💻 CLI Commands & Options

```text
Usage: firn <path-to-markdown> [options]
       firn [directory] [options]

Options:
  -p, --port PORT        Bind specific localhost port (default: random ephemeral port)
  --host HOST            Bind address for grip daemon (default: 127.0.0.1)
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
```

### ⌨️ Window Keyboard Shortcuts

| Keybinding | Action |
| :--- | :--- |
| `q` / `Esc` / `Ctrl+W` | Close window & terminate ephemeral `grip` daemon |
| `t` | Toggle between GitHub Dark and Light themes |
| `r` / `F5` / `Ctrl+R` | Reload Markdown document |
| `Ctrl + +` / `Ctrl + -` | Zoom in / Zoom out |
| `Ctrl + 0` | Reset zoom level to 100% |

---

## ❄️ Frost & Home Manager Integration

### Home Manager Standalone

Add Firn to your `flake.nix`:

```nix
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    firn = {
      url = "github:SpanishSyntax/Firn";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, firn, ... }: {
    homeConfigurations.user = home-manager.lib.homeManagerConfiguration {
      modules = [
        firn.homeManagerModules.default
        {
          programs.firn.enable = true;
        }
      ];
    };
  };
}
```

### Frost Iceberg Module (`home/applications/icebergs/firn.nix`)

In **Frost**, add `firn` to your flake inputs and enable the iceberg module:

```nix
{
  config,
  lib,
  inputs,
  ...
}: let
  cfg = config.frost.home.apps.icebergs.firn;
in {
  imports = [inputs.firn.homeManagerModules.default];

  options.frost.home.apps.icebergs.firn = {
    enable = lib.mkEnableOption "Firn instant GFM native desktop viewer";
  };

  config = lib.mkIf cfg.enable {
    programs.firn.enable = true;
  };
}
```

Then enable it in your Frost host/home configuration:

```nix
frost.home.apps.icebergs.firn.enable = true;
```

---

## 📜 License

MIT © SpanishSyntax
