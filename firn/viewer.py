"""Pywebview native window wrapper, GFM parity enhancer (Alerts, Math, Mermaid), and lifecycle manager."""

import json
import os
from typing import Any

from firn.core import GripOrchestrator, RenderConfig
from firn.ui import ui

GFM_PARITY_CSS = """
/* Firn Crystalline Minimal Frame & GitHub Callout / Alert Parity */
:root {
  --firn-note: #0969da;
  --firn-tip: #1a7f37;
  --firn-important: #8250df;
  --firn-warning: #9a6700;
  --firn-caution: #cf222e;
}

html[data-color-mode="dark"] {
  color-scheme: dark;
  --firn-note: #2f81f7;
  --firn-tip: #3fb950;
  --firn-important: #a371f7;
  --firn-warning: #d29922;
  --firn-caution: #f85149;
  background-color: #0d1117 !important;
  color: #e6edf3 !important;
}

html[data-color-mode="dark"] body,
html[data-color-mode="dark"] .page {
  background-color: #0d1117 !important;
  color: #e6edf3 !important;
}

html[data-color-mode="dark"] .markdown-body {
  color-scheme: dark;
  background-color: #0d1117 !important;
  color: #e6edf3 !important;
}

html[data-color-mode="dark"] . boxed-group > h3,
html[data-color-mode="dark"] #readme .Box-header,
html[data-color-mode="dark"] .Box-header {
  background-color: #161b22 !important;
  border-color: #30363d !important;
  color: #e6edf3 !important;
}

html[data-color-mode="dark"] #readme .Box,
html[data-color-mode="dark"] .Box,
html[data-color-mode="dark"] . boxed-group-inner {
  background-color: #0d1117 !important;
  border-color: #30363d !important;
}

html[data-color-mode="dark"] .markdown-body pre,
html[data-color-mode="dark"] .markdown-body code,
html[data-color-mode="dark"] .markdown-body .highlight pre {
  background-color: #161b22 !important;
  color: #e6edf3 !important;
}

html[data-color-mode="dark"] .markdown-body table tr {
  background-color: #0d1117 !important;
  border-top-color: #30363d !important;
}

html[data-color-mode="dark"] .markdown-body table tr:nth-child(2n) {
  background-color: #161b22 !important;
}

html[data-color-mode="dark"] .markdown-body table th,
html[data-color-mode="dark"] .markdown-body table td {
  border-color: #30363d !important;
}

html[data-color-mode="dark"] .markdown-body h1,
html[data-color-mode="dark"] .markdown-body h2 {
  border-bottom-color: #21262d !important;
}

html[data-color-mode="dark"] .markdown-body hr {
  background-color: #30363d !important;
}

html[data-color-mode="dark"] .markdown-body blockquote {
  color: #8b949e !important;
  border-left-color: #30363d !important;
}

html[data-color-mode="dark"] .markdown-body a {
  color: #58a6ff !important;
}

/* Default Clean Document Mode: strip Grip's phantom GitHub sidebar grid and nested Box chrome */
html:not([data-firn-layout="github"]),
html:not([data-firn-layout="github"]) body,
html:not([data-firn-layout="github"]) .page {
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
  min-height: 100vh !important;
}

html:not([data-firn-layout="github"]) .preview-page {
  margin: 0 !important;
  padding: 0 !important;
}

html:not([data-firn-layout="github"]) .container,
html:not([data-firn-layout="github"]) .container-lg,
html:not([data-firn-layout="github"]) .container-xl,
html:not([data-firn-layout="github"]) .new-discussion-timeline,
html:not([data-firn-layout="github"]) .repository-content {
  max-width: 100% !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
}

html:not([data-firn-layout="github"]) .Layout,
html:not([data-firn-layout="github"]) .Layout-main {
  display: block !important;
  grid-template-columns: 1fr !important;
  width: 100% !important;
  max-width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
}

html:not([data-firn-layout="github"]) #readme,
html:not([data-firn-layout="github"]) .Box,
html:not([data-firn-layout="github"]) .Box--responsive {
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
  max-width: 100% !important;
}

html:not([data-firn-layout="github"]) #readme .Box-header,
html:not([data-firn-layout="github"]) .Box-header {
  display: none !important;
}

html:not([data-firn-layout="github"]) #readme .Box-body,
html:not([data-firn-layout="github"]) .Box-body {
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
}

html:not([data-firn-layout="github"]) #grip-content.markdown-body,
html:not([data-firn-layout="github"]) .markdown-body.entry-content {
  max-width: 100% !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 24px 32px !important;
  box-sizing: border-box !important;
}

/* GitHub Alert / Callout Styling */
.markdown-alert {
  padding: 0.5rem 1rem;
  margin-bottom: 16px;
  color: inherit;
  border-left: 0.25em solid #8b949e;
  border-radius: 0 6px 6px 0;
}

.markdown-alert > :first-child { margin-top: 0; }
.markdown-alert > :last-child { margin-bottom: 0; }

.markdown-alert .markdown-alert-title {
  display: flex;
  font-weight: 600;
  align-items: center;
  line-height: 1;
  margin-bottom: 4px;
}

.markdown-alert .markdown-alert-title svg {
  margin-right: 8px;
  fill: currentColor;
}

.markdown-alert.markdown-alert-note {
  border-left-color: var(--firn-note);
  background-color: rgba(9, 105, 218, 0.06);
}
.markdown-alert.markdown-alert-note .markdown-alert-title { color: var(--firn-note); }

.markdown-alert.markdown-alert-tip {
  border-left-color: var(--firn-tip);
  background-color: rgba(26, 127, 55, 0.06);
}
.markdown-alert.markdown-alert-tip .markdown-alert-title { color: var(--firn-tip); }

.markdown-alert.markdown-alert-important {
  border-left-color: var(--firn-important);
  background-color: rgba(130, 80, 223, 0.06);
}
.markdown-alert.markdown-alert-important .markdown-alert-title { color: var(--firn-important); }

.markdown-alert.markdown-alert-warning {
  border-left-color: var(--firn-warning);
  background-color: rgba(154, 103, 0, 0.06);
}
.markdown-alert.markdown-alert-warning .markdown-alert-title { color: var(--firn-warning); }

.markdown-alert.markdown-alert-caution {
  border-left-color: var(--firn-caution);
  background-color: rgba(207, 34, 46, 0.06);
}
.markdown-alert.markdown-alert-caution .markdown-alert-title { color: var(--firn-caution); }

.firn-mermaid-diagram {
  display: flex;
  justify-content: center;
  margin: 16px 0;
  padding: 12px;
  overflow-x: auto;
}
"""

GFM_PARITY_JS = """
(function() {
  if (window.__firnEnhanced) return;
  window.__firnEnhanced = true;

  const themePref = __FIRN_THEME__;
  const initialLayout = __FIRN_LAYOUT__;

  const applyTheme = (mode) => {
    let resolved = mode;
    if (mode === "auto") {
      resolved = (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches)
        ? "dark" : "light";
    }
    document.documentElement.setAttribute("data-color-mode", resolved);
    document.documentElement.setAttribute("data-light-theme", "light");
    document.documentElement.setAttribute("data-dark-theme", "dark");
    window.__firnCurrentTheme = resolved;
  };

  const applyLayout = (layout) => {
    document.documentElement.setAttribute("data-firn-layout", layout);
    window.__firnCurrentLayout = layout;
  };

  applyTheme(themePref);
  applyLayout(initialLayout);

  const alertTypes = {
    NOTE: { cls: "markdown-alert-note", label: "Note" },
    TIP: { cls: "markdown-alert-tip", label: "Tip" },
    IMPORTANT: { cls: "markdown-alert-important", label: "Important" },
    WARNING: { cls: "markdown-alert-warning", label: "Warning" },
    CAUTION: { cls: "markdown-alert-caution", label: "Caution" }
  };

  let isEnhancing = false;
  const enhanceContent = () => {
    if (isEnhancing) return;
    isEnhancing = true;
    try {
      // Transform any raw blockquote [!NOTE] / [!TIP] / [!IMPORTANT] / [!WARNING] / [!CAUTION]
      document.querySelectorAll(".markdown-body blockquote").forEach((bq) => {
        const firstP = bq.querySelector("p:first-child");
        if (!firstP) return;
        const match = firstP.innerHTML.match(/^\\s*\\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\\]\\s*(?:<br\\s*\\/?>|\\n)?/i);
        if (!match) return;
        const key = match[1].toUpperCase();
        const info = alertTypes[key];
        if (!info) return;

        firstP.innerHTML = firstP.innerHTML.slice(match[0].length);
        const wrapper = document.createElement("div");
        wrapper.className = "markdown-alert " + info.cls;
        const titleEl = document.createElement("p");
        titleEl.className = "markdown-alert-title";
        titleEl.textContent = info.label;
        wrapper.appendChild(titleEl);
        while (bq.firstChild) {
          wrapper.appendChild(bq.firstChild);
        }
        bq.replaceWith(wrapper);
      });

      // Mermaid diagram support
      const mermaidBlocks = document.querySelectorAll(
        'pre[lang="mermaid"], div.highlight-source-mermaid pre, code.language-mermaid'
      );
      if (mermaidBlocks.length > 0) {
        const renderMermaid = () => {
          const mTheme = window.__firnCurrentTheme === "dark" ? "dark" : "default";
          window.mermaid.initialize({ startOnLoad: false, theme: mTheme, securityLevel: "loose" });
          mermaidBlocks.forEach((block, idx) => {
            const container = block.closest("div.highlight-source-mermaid") || block.closest("pre") || block;
            const source = block.textContent || "";
            const target = document.createElement("div");
            target.className = "mermaid firn-mermaid-diagram";
            target.id = "firn-mermaid-" + Date.now() + "-" + idx;
            target.textContent = source;
            container.replaceWith(target);
          });
          window.mermaid.run({ querySelector: ".firn-mermaid-diagram" });
        };
        if (window.mermaid) {
          renderMermaid();
        } else {
          const script = document.createElement("script");
          script.src = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js";
          script.onload = renderMermaid;
          document.head.appendChild(script);
        }
      }

      // KaTeX math support for inline ($...$) and block ($$...$$) / GitHub math-renderer tags
      const hasMath = document.querySelector("math-renderer, .js-inline-math, .js-display-math, code.language-math")
        || /\\$\\$[\\s\\S]+?\\$\\$|\\$[^$\\n]+?\\$/.test(document.querySelector(".markdown-body")?.innerHTML || "");
      if (hasMath) {
        const runKatex = () => {
          const body = document.querySelector(".markdown-body") || document.body;
          window.renderMathInElement(body, {
            delimiters: [
              { left: "$$", right: "$$", display: true },
              { left: "$", right: "$", display: false },
              { left: "\\\\(", right: "\\\\)", display: false },
              { left: "\\\\[", right: "\\\\]", display: true }
            ],
            throwOnError: false
          });
        };
        if (window.renderMathInElement) {
          runKatex();
        } else {
          const katexCss = document.createElement("link");
          katexCss.rel = "stylesheet";
          katexCss.href = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css";
          document.head.appendChild(katexCss);

          const katexJs = document.createElement("script");
          katexJs.src = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js";
          katexJs.onload = () => {
            const autoRender = document.createElement("script");
            autoRender.src = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js";
            autoRender.onload = runKatex;
            document.head.appendChild(autoRender);
          };
          document.head.appendChild(katexJs);
        }
      }
    } finally {
      isEnhancing = false;
    }
  };

  enhanceContent();

  const gripArticle = document.getElementById("grip-content");
  if (gripArticle && window.MutationObserver) {
    const observer = new MutationObserver(() => enhanceContent());
    observer.observe(gripArticle, { childList: true });
  }

  // Keyboard navigation & shortcuts inside native Firn window
  let zoomLevel = 1.0;
  window.addEventListener("keydown", (ev) => {
    const tag = (ev.target && ev.target.tagName) ? ev.target.tagName.toLowerCase() : "";
    const inInput = tag === "input" || tag === "textarea" || (ev.target && ev.target.isContentEditable);

    if ((ev.ctrlKey && (ev.key === "q" || ev.key === "w")) || (!inInput && (ev.key === "q" || ev.key === "Escape"))) {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.close_window) {
        ev.preventDefault();
        window.pywebview.api.close_window();
      }
    } else if (!inInput && ev.key === "t" && !ev.ctrlKey && !ev.metaKey) {
      const next = window.__firnCurrentTheme === "dark" ? "light" : "dark";
      applyTheme(next);
    } else if (!inInput && ev.key === "g" && !ev.ctrlKey && !ev.metaKey) {
      const nextLayout = window.__firnCurrentLayout === "github" ? "clean" : "github";
      applyLayout(nextLayout);
    } else if ((!inInput && ev.key === "r" && !ev.ctrlKey) || ev.key === "F5" || (ev.ctrlKey && ev.key === "r")) {
      ev.preventDefault();
      window.location.reload();
    } else if (ev.ctrlKey && (ev.key === "=" || ev.key === "+")) {
      ev.preventDefault();
      zoomLevel = Math.min(2.5, zoomLevel + 0.1);
      document.body.style.zoom = String(zoomLevel);
    } else if (ev.ctrlKey && ev.key === "-") {
      ev.preventDefault();
      zoomLevel = Math.max(0.5, zoomLevel - 0.1);
      document.body.style.zoom = String(zoomLevel);
    } else if (ev.ctrlKey && ev.key === "0") {
      ev.preventDefault();
      zoomLevel = 1.0;
      document.body.style.zoom = "1.0";
    }
  });
})();
"""


class FirnBridge:
    """JS-to-Python API exposed to the pywebview frame."""

    def __init__(self, orchestrator: GripOrchestrator):
        self._orchestrator = orchestrator
        self._window: Any = None

    def attach_window(self, window: Any):
        self._window = window

    def close_window(self):
        """Closes the native pywebview window and stops the grip daemon."""
        self._orchestrator.stop()
        if self._window is not None:
            try:
                self._window.destroy()
            except Exception:
                pass


def launch_viewer(orchestrator: GripOrchestrator, config: RenderConfig):
    """
    Launches the ephemeral pywebview window pointing at the local grip server
    and guarantees immediate cleanup when the window closes.
    """
    try:
        import webview  # type: ignore[import-untyped]
    except ImportError as exc:
        orchestrator.stop()
        raise RuntimeError(
            f"pywebview is not available in the current Python environment: {exc}"
        ) from exc

    window_title = config.title or f"Firn: {config.target_path.name}"
    bridge = FirnBridge(orchestrator)

    bg_color = "#0d1117" if config.theme == "dark" else "#ffffff"

    window = webview.create_window(
        title=window_title,
        url=orchestrator.url,
        width=config.width,
        height=config.height,
        frameless=config.frameless,
        easy_drag=config.frameless,
        background_color=bg_color,
        text_select=True,
        js_api=bridge,
    )
    bridge.attach_window(window)

    layout_mode = "github" if config.github_mode else "clean"

    def _on_loaded():
        try:
            window.load_css(GFM_PARITY_CSS)
            js_payload = GFM_PARITY_JS.replace(
                "__FIRN_THEME__", json.dumps(config.theme)
            ).replace("__FIRN_LAYOUT__", json.dumps(layout_mode))
            window.evaluate_js(js_payload)
        except Exception:
            pass

    def _on_closed():
        orchestrator.stop()

    window.events.loaded += _on_loaded
    window.events.closed += _on_closed

    gui_backend = os.environ.get("PYWEBVIEW_GUI")
    ui.action(
        f"Opening native window '{ui.bold(window_title)}' ({config.width}×{config.height})"
        + (f" [{gui_backend}]" if gui_backend else ""),
        symbol="🪟",
    )
    ui.info(
        "Shortcuts: [q / Esc] Close  •  [t] Theme  •  [g] GitHub Box Layout  •  [r / F5] Reload  •  [Ctrl +/-] Zoom",
        symbol="💡",
    )

    try:
        webview.start(debug=config.debug, gui=gui_backend if gui_backend else None)
    finally:
        orchestrator.stop()
