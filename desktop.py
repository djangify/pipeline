"""
Pipeline desktop launcher.

Runs the Django app on a local production server (waitress) in a background
thread and displays it inside a native desktop window using PyWebView, so
you get an app window instead of a browser tab or a terminal command.

Run in development:   python desktop.py
Packaged as an .exe:  this file is the PyInstaller entry point (see
                       pipeline.spec)
"""

import os
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path


def _writable_data_dir() -> Path:
    """Match the DATA_DIR logic in config/settings.py so we can store a secret key."""
    if os.environ.get("PIPELINE_DATA_DIR"):
        return Path(os.environ["PIPELINE_DATA_DIR"])
    if getattr(sys, "frozen", False):
        # Not AppData -- see the DATA_DIR comment in config/settings.py.
        return Path.home() / "Pipeline Data"
    return Path(__file__).resolve().parent / "data"


def _legacy_data_dir() -> Path:
    """Where packaged builds kept their data before moving to "Pipeline Data"."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "Pipeline"


def _copy_legacy_data(data_dir: Path) -> None:
    """One-time move of an existing install's database, media and SECRET_KEY
    from the old AppData location. Copies rather than moves, so the old folder
    stays as a backup. Only Pipeline.exe calls this: it is started by the user,
    so it sees the real AppData, whereas Pipeline-mcp.exe is started by Claude
    Desktop and would see Claude's virtualized copy instead."""
    import shutil

    if not getattr(sys, "frozen", False) or os.environ.get("PIPELINE_DATA_DIR"):
        return
    legacy = _legacy_data_dir()
    if (data_dir / "db" / "db.sqlite3").exists() or not (legacy / "db" / "db.sqlite3").exists():
        return
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        for name in ("db", "media"):
            if (legacy / name).is_dir():
                shutil.copytree(legacy / name, data_dir / name, dirs_exist_ok=True)
        if (legacy / "secret_key.txt").exists():
            shutil.copy2(legacy / "secret_key.txt", data_dir / "secret_key.txt")
        _append_log(data_dir, "startup.log", f"copied existing data from {legacy}")
    except Exception as exc:
        _append_log(data_dir, "startup.log", f"copy from {legacy} failed: {exc}")


def _ensure_secret_key(data_dir: Path) -> None:
    """
    Make sure a SECRET_KEY is available. In a packaged build there's no .env,
    so we generate one once and persist it in the user's data folder.
    """
    if os.environ.get("SECRET_KEY"):
        return
    if (Path(__file__).resolve().parent / ".env").exists() and not getattr(
        sys, "frozen", False
    ):
        # Dev run with a .env present -- let settings read it.
        return
    key_file = data_dir / "secret_key.txt"
    try:
        if key_file.exists():
            os.environ["SECRET_KEY"] = key_file.read_text(encoding="utf-8").strip()
        else:
            from django.core.management.utils import get_random_secret_key

            key = get_random_secret_key()
            data_dir.mkdir(parents=True, exist_ok=True)
            key_file.write_text(key, encoding="utf-8")
            os.environ["SECRET_KEY"] = key
    except Exception:
        # Fall back to settings' built-in default if anything goes wrong.
        pass


def _resource_path(rel: str) -> str:
    """Resolve a bundled resource path (works in dev and in the frozen .exe)."""
    base = getattr(sys, "_MEIPASS", None) or str(Path(__file__).resolve().parent)
    return str(Path(base) / rel)


def _append_log(data_dir: Path, filename: str, message: str) -> None:
    """Append one timestamped line to a small log in the data folder, so
    startup problems are visible in the windowed build (console=False, so
    print() goes nowhere). Best-effort -- never raises."""
    try:
        import datetime

        data_dir.mkdir(parents=True, exist_ok=True)
        line = f"{datetime.datetime.now().isoformat(timespec='seconds')}  {message}\n"
        with open(data_dir / filename, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass


def _connect_claude_once(data_dir: Path) -> str:
    """One reconcile attempt against Claude Desktop's config: adds or repoints
    the "pipeline" mcpServers entry and records the outcome in
    claude_connect_state.json. Returns the status string. Never raises."""
    try:
        from mcp_server.desktop_connect import connect_and_record

        frozen = getattr(sys, "frozen", False)
        base_dir = Path(__file__).resolve().parent
        return connect_and_record(data_dir, base_dir, frozen)
    except Exception as exc:
        return f"error: {type(exc).__name__}: {exc}"


def _start_claude_connect_watch(data_dir: Path) -> None:
    """Register this install as an MCP server in Claude Desktop now, and if
    Claude isn't visible yet, keep retrying in the background so installing or
    opening Claude *after* this app still connects with no relaunch. The
    reconcile is idempotent, so retrying is safe. Daemon thread -- never blocks
    or crashes startup. Logs to claude_connect.log only when the status
    changes."""

    def _watch() -> None:
        fast_deadline = time.time() + 300  # 5 min at 5s, then back off to 60s
        last_logged = None
        while True:
            status = _connect_claude_once(data_dir)
            if status != last_logged:
                _append_log(data_dir, "claude_connect.log", f"connect() -> {status}")
                last_logged = status
            if not status.startswith("no-claude"):
                return  # connected/updated/unchanged, or a hard error -- done.
            time.sleep(5 if time.time() < fast_deadline else 60)

    threading.Thread(target=_watch, daemon=True).start()


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_until_ready(url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status < 500:
                    return True
        except Exception:
            time.sleep(0.25)
    return False


def main() -> None:
    # --- Environment: desktop mode, served locally over http on loopback ---
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ["PIPELINE_DESKTOP"] = "1"
    # DEBUG=True keeps things simple for a local single-user app: it serves
    # media files and avoids the HTTPS redirect that production mode forces.
    os.environ.setdefault("DEBUG", "True")

    data_dir = _writable_data_dir()
    _copy_legacy_data(data_dir)
    _ensure_secret_key(data_dir)

    import django

    django.setup()

    # --- Apply any pending database migrations on startup ---
    from django.core.management import call_command

    try:
        call_command("migrate", interactive=False, verbosity=0)
    except Exception as exc:  # pragma: no cover - surfaced to the user
        print(f"Database setup failed: {exc}")

    # Make sure a login exists on a fresh install (demo@example.com / demo123,
    # or whatever DEFAULT_USER_EMAIL/PASSWORD are set to). Safe to run every
    # time -- it does nothing if a user already exists.
    try:
        call_command("create_default_user", verbosity=0)
    except Exception as exc:  # pragma: no cover
        print(f"Could not create the default user: {exc}")

    # Register this install as an MCP server so Claude Desktop can read and
    # add contacts (see mcp_server/). Reconciles immediately and keeps retrying
    # in the background if Claude Desktop isn't installed/visible yet.
    _start_claude_connect_watch(data_dir)

    # --- Start the web server in a background thread ---
    from waitress import serve
    from config.wsgi import application

    port = _find_free_port()
    host = "127.0.0.1"
    url = f"http://{host}:{port}/"

    server_thread = threading.Thread(
        target=lambda: serve(application, host=host, port=port, threads=8),
        daemon=True,
    )
    server_thread.start()

    if not _wait_until_ready(url, timeout=30):
        print("Pipeline server did not start in time.")
        # Still try to open the window; it will show an error if truly dead.

    # --- Open the native window ---
    import webview

    webview.create_window(
        "Pipeline",
        url,
        width=1280,
        height=860,
        min_size=(900, 600),
    )

    # Window icon, if one has been bundled (see pipeline.spec). Guarded so an
    # unsupported backend, or a missing icon, can never stop the app launching.
    icon_path = _resource_path("static/images/pipeline.ico")
    try:
        if os.path.exists(icon_path):
            webview.start(icon=icon_path)
        else:
            webview.start()
    except TypeError:
        # Older/unsupported backends don't accept the icon argument.
        webview.start()

    # Window closed -- exit immediately (daemon server thread is torn down).
    os._exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # console=False in the shipped build means errors normally vanish with
        # the window. This makes sure that never happens silently: print the
        # traceback and, if there's a console attached (a debug build), wait
        # so it's actually readable before the window closes.
        import traceback

        traceback.print_exc()
        try:
            input("\nPipeline failed to start. Press Enter to close...")
        except Exception:
            pass
        raise
