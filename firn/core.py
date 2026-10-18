"""Process orchestrator: ephemeral port binding, token discovery, grip daemon lifecycle, and signal trapping."""

import atexit
import ctypes
import os
import shutil
import signal
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from firn.ui import ui

PR_SET_PDEATHSIG = 1

STANDARD_PASS_PATHS = (
    "github/token",
    "github/pat",
    "github/api-token",
    "github/personal-access-token",
    "dev/github/token",
)


class GripStartupError(RuntimeError):
    """Raised when the background grip server fails to initialize or bind."""


@dataclass
class RenderConfig:
    """Configuration for a Firn document viewing session."""

    target_path: Path
    host: str = "127.0.0.1"
    port: int = 0
    wide: bool = False
    user_content: bool = False
    context: str | None = None
    title: str | None = None
    api_url: str | None = None
    token: str | None = None
    pass_path: str | None = None
    no_inline: bool = True
    frameless: bool = False
    github_mode: bool = False
    theme: str = "auto"  # auto, dark, light
    width: int = 980
    height: int = 860
    debug: bool = False


def find_ephemeral_port(host: str = "127.0.0.1") -> int:
    """Binds to port 0 on localhost to let the kernel assign an unprivileged ephemeral port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _query_pass_store(entry: str) -> str | None:
    """Queries the standard Unix password-store (`pass`) non-interactively."""
    if not shutil.which("pass"):
        return None

    store_dir = Path(
        os.environ.get("PASSWORD_STORE_DIR", Path.home() / ".password-store")
    )
    gpg_file = store_dir / f"{entry}.gpg"
    if not gpg_file.exists():
        return None

    env = os.environ.copy()
    env.setdefault("PINENTRY_USER_DATA", "USE_CURSES=0")

    try:
        res = subprocess.run(
            ["pass", "show", entry],
            capture_output=True,
            text=True,
            timeout=2.5,
            stdin=subprocess.DEVNULL,
            env=env,
        )
        if res.returncode == 0 and res.stdout.strip():
            first_line = res.stdout.strip().splitlines()[0].strip()
            if first_line:
                return first_line
    except (subprocess.SubprocessError, OSError):
        pass
    return None


def resolve_github_token(
    explicit_token: str | None = None,
    pass_path: str | None = None,
) -> tuple[str | None, str]:
    """
    Resolves an optional GitHub Personal Access Token to bypass the 60 req/hr anonymous API limit.
    Returns (token, source_description).
    """
    if explicit_token and explicit_token.strip():
        return explicit_token.strip(), "CLI --token"

    for env_var in ("GITHUB_TOKEN", "GRIP_TOKEN", "GH_TOKEN", "FIRN_GITHUB_TOKEN"):
        val = os.environ.get(env_var, "").strip()
        if val:
            return val, f"env:{env_var}"

    xdg_cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    token_file = xdg_cfg / "firn" / "token"
    if token_file.is_file():
        try:
            content = token_file.read_text(encoding="utf-8").strip().splitlines()
            if content and content[0].strip():
                return content[0].strip(), f"file:{token_file}"
        except OSError:
            pass

    pass_candidates: list[str] = []
    if pass_path:
        pass_candidates.append(pass_path)
    env_pass = os.environ.get("FIRN_PASS_PATH", "").strip()
    if env_pass and env_pass not in pass_candidates:
        pass_candidates.append(env_pass)
    for std_path in STANDARD_PASS_PATHS:
        if std_path not in pass_candidates:
            pass_candidates.append(std_path)

    for candidate in pass_candidates:
        tok = _query_pass_store(candidate)
        if tok:
            return tok, f"pass:{candidate}"

    if shutil.which("gh"):
        try:
            res = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=2.0,
                stdin=subprocess.DEVNULL,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip(), "gh-cli"
        except (subprocess.SubprocessError, OSError):
            pass

    return None, "anonymous (60 req/hr)"


def _linux_set_pdeathsig():
    """
    Sets PR_SET_PDEATHSIG(SIGTERM) on the child process on Linux so the kernel
    automatically terminates grip even if the parent Python process is SIGKILLed.
    """
    try:
        os.setsid()
    except OSError:
        pass
    if os.uname().sysname == "Linux":
        try:
            libc = ctypes.CDLL("libc.so.6", use_errno=True)
            libc.prctl(PR_SET_PDEATHSIG, signal.SIGTERM)
        except Exception:
            pass


class GripOrchestrator:
    """Manages the ephemeral grip background server and guarantees strict teardown."""

    def __init__(self, config: RenderConfig):
        self.config = config
        self.port: int = config.port or find_ephemeral_port(config.host)
        self.process: subprocess.Popen[str] | None = None
        self._cleaned_up = False
        self._prev_handlers: dict[int, Any] = {}

    @property
    def url(self) -> str:
        return f"http://{self.config.host}:{self.port}/"

    def _build_command(self, token: str | None, include_no_inline: bool = True) -> list[str]:
        grip_bin = shutil.which("grip")
        if not grip_bin:
            raise GripStartupError(
                "Could not find 'grip' executable in PATH. Ensure Firn is run via its Nix wrapper or devShell."
            )

        address = f"{self.config.host}:{self.port}"
        cmd = [grip_bin, str(self.config.target_path), address, "--quiet"]

        if include_no_inline and self.config.no_inline:
            cmd.append("--no-inline")

        if self.config.wide:
            cmd.append("--wide")

        if self.config.user_content:
            cmd.append("--user-content")

        if self.config.context:
            cmd.append(f"--context={self.config.context}")

        doc_title = self.config.title or f"Firn: {self.config.target_path.name}"
        cmd.append(f"--title={doc_title}")

        if self.config.api_url:
            cmd.append(f"--api-url={self.config.api_url}")

        if token:
            cmd.append(f"--pass={token}")

        return cmd

    def _install_signal_traps(self):
        atexit.register(self.stop)

        def _trap_handler(signum: int, _frame: Any):
            ui.warn(f"Caught signal {signal.Signals(signum).name}, terminating grip daemon...")
            self.stop()
            raise SystemExit(128 + signum)

        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
            try:
                self._prev_handlers[sig] = signal.getsignal(sig)
                signal.signal(sig, _trap_handler)
            except (ValueError, OSError):
                pass

    def _restore_signal_traps(self):
        for sig, prev in self._prev_handlers.items():
            try:
                signal.signal(sig, prev)
            except (ValueError, OSError):
                pass
        self._prev_handlers.clear()

    def _spawn_and_wait(
        self, cmd: list[str], timeout: float = 12.0
    ) -> tuple[bool, str]:
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            cwd=str(self.config.target_path.parent),
            preexec_fn=_linux_set_pdeathsig,
        )

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            ret = self.process.poll()
            if ret is not None:
                _, err_out = self.process.communicate(timeout=1.0)
                return False, (err_out or "").strip()

            try:
                with socket.create_connection(
                    (self.config.host, self.port), timeout=0.15
                ):
                    return True, ""
            except OSError:
                time.sleep(0.05)

        return False, "Timed out waiting for grip local HTTP server to bind."

    def start(self):
        """Resolves token, installs signal traps, and launches the background grip daemon."""
        if not self.config.target_path.exists():
            raise GripStartupError(
                f"Target Markdown file not found: {self.config.target_path}"
            )

        token, token_source = resolve_github_token(
            explicit_token=self.config.token,
            pass_path=self.config.pass_path,
        )

        ui.info(
            f"Target: {ui.cyan(self.config.target_path.name)} | Endpoint: {ui.bold_cyan(self.url)} | Auth: {ui.green(token_source) if token else ui.yellow(token_source)}",
            symbol="📄",
        )

        self._install_signal_traps()
        self._cleaned_up = False

        cmd = self._build_command(token, include_no_inline=True)
        with ui.spinner(
            f"Rendering '{self.config.target_path.name}' via GitHub Markdown API..."
        ) as sp:
            ok, err_text = self._spawn_and_wait(cmd)
            if not ok and self.config.no_inline and "usage:" in err_text.lower():
                sp.update(
                    f"Retrying '{self.config.target_path.name}' render pipeline..."
                )
                cmd_fallback = self._build_command(token, include_no_inline=False)
                ok, err_text = self._spawn_and_wait(cmd_fallback)

        if not ok:
            self.stop()
            details = err_text or "Unknown grip startup error."
            raise GripStartupError(details)

        pid = self.process.pid if self.process else "?"
        ui.success(
            f"Grip daemon active (PID {pid}) serving {self.config.target_path.name}"
        )

    def stop(self):
        """Immediately terminates the grip subprocess and its process group."""
        if self._cleaned_up:
            return
        self._cleaned_up = True

        proc = self.process
        self.process = None
        if proc is None:
            self._restore_signal_traps()
            return

        if proc.poll() is None:
            pgid = None
            try:
                pgid = os.getpgid(proc.pid)
            except OSError:
                pass

            try:
                if pgid is not None and pgid > 1:
                    os.killpg(pgid, signal.SIGTERM)
                else:
                    proc.terminate()
            except OSError:
                pass

            try:
                proc.wait(timeout=1.5)
            except subprocess.TimeoutExpired:
                try:
                    if pgid is not None and pgid > 1:
                        os.killpg(pgid, signal.SIGKILL)
                    else:
                        proc.kill()
                except OSError:
                    pass
                try:
                    proc.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    pass

        for stream in (proc.stdout, proc.stderr):
            if stream:
                try:
                    stream.close()
                except OSError:
                    pass

        self._restore_signal_traps()
        ui.info("Ephemeral grip daemon terminated cleanly.", symbol="🛑")

    def __enter__(self) -> "GripOrchestrator":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        self.stop()
