# mcp_server/desktop_connect.py
"""Register this install as an MCP server in the user's Claude Desktop config.

Lets a fresh install connect to Claude Desktop automatically on first launch,
so a non-technical owner never has to hand-edit a JSON file. Everything here is
best-effort and must never raise into the app's startup path — callers get a
short status string instead.

There is no "account" to connect to: an MCP server is just a local config entry
telling Claude Desktop which program to launch. So this is safe and reversible —
the owner can remove the entry in Claude Desktop at any time.
"""
import datetime
import json
import os
import sys
from pathlib import Path

SERVER_NAME = "pipeline"

# Small JSON file in the app's writable data dir that records the outcome of the
# last connect attempt, so the running web app can show an accurate, persistent
# connection status instead of a one-shot URL flag that vanishes on navigation.
STATE_FILE = "claude_connect_state.json"

_DEFAULT_STATE = {
    "status": "unknown",       # last connect() result
    "connected": False,        # have we EVER successfully written/confirmed the entry
    "restart_pending": False,  # connected/updated but Claude not yet restarted
    "config_path": "",         # where the entry was written
    "updated_at": "",          # ISO timestamp of the last attempt
}

# Statuses that mean the mcpServers entry is present and correct.
CONNECTED_STATUSES = ("connected", "updated", "unchanged")


def state_path(data_dir) -> Path:
    return Path(data_dir) / STATE_FILE


def read_state(data_dir) -> dict:
    """Best-effort read of the persisted connection state. Never raises —
    returns sensible defaults when the file is missing or unreadable."""
    state = dict(_DEFAULT_STATE)
    try:
        path = state_path(data_dir)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                state.update({k: data[k] for k in data if k in _DEFAULT_STATE})
    except Exception:
        pass
    return state


def _write_state(data_dir, state: dict) -> None:
    """Persist the connection state. Best-effort — never raises."""
    try:
        path = state_path(data_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass


def record_connect(data_dir, status: str, cfg_path=None) -> dict:
    """Update the persisted state after a connect() attempt and return it.

    A fresh connection (or a changed one) flips restart_pending on, because
    Claude Desktop only loads mcpServers at startup and must be relaunched.
    'unchanged' leaves restart_pending as it was — so a pending restart the owner
    hasn't acknowledged is never lost, and an already-acknowledged connection
    doesn't nag on every launch. A 'no-claude' result means Claude Desktop is
    gone, so both connected and restart_pending are cleared; an 'error' result is
    ambiguous and leaves both untouched.
    """
    state = read_state(data_dir)
    state["status"] = status
    if cfg_path:
        state["config_path"] = str(cfg_path)
    state["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    if status in ("connected", "updated"):
        state["restart_pending"] = True
    if status in CONNECTED_STATUSES:
        state["connected"] = True
    elif status.startswith("no-claude"):
        # Claude Desktop isn't installed/visible, so the config entry can't be
        # active — report "not connected" truthfully instead of latching a stale
        # True from an earlier session. connect()'s folder probe already retries
        # before returning no-claude, so this result is authoritative, not a
        # one-off flake. And there's nothing to restart when Claude isn't there,
        # so drop any pending-restart nag too.
        state["connected"] = False
        state["restart_pending"] = False
    # An "error:" result is genuinely ambiguous (couldn't read or write the
    # config; the entry may still be present), so it leaves connected and
    # restart_pending untouched rather than guessing.
    _write_state(data_dir, state)
    return state


def clear_restart_pending(data_dir) -> dict:
    """Owner has confirmed they've restarted Claude Desktop — stop nagging."""
    state = read_state(data_dir)
    state["restart_pending"] = False
    _write_state(data_dir, state)
    return state


def connect_and_record(data_dir, base_dir: Path, frozen: bool, *,
                       config_path: "Path | None" = None,
                       name: str = SERVER_NAME) -> str:
    """connect(), then persist the outcome so the UI reflects it. Returns the
    same status string as connect()."""
    status = connect(base_dir, frozen, config_path=config_path, name=name)
    cfg = config_path or claude_config_path()
    record_connect(data_dir, status, cfg)
    return status


def claude_config_path() -> Path | None:
    """Location of claude_desktop_config.json for this OS, or None if unknown."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        return Path(base) / "Claude" / "claude_desktop_config.json" if base else None
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    # Linux (community Claude Desktop builds) — best effort.
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def claude_desktop_present(config_path: Path | None = None) -> bool:
    """True if Claude Desktop looks installed (its config directory exists)."""
    path = config_path or claude_config_path()
    return bool(path and path.parent.exists())


def server_entry(base_dir: Path, frozen: bool) -> dict:
    """The mcpServers entry to install — correct for a packaged .exe vs dev."""
    if frozen:
        # Packaged: point at the sibling console MCP executable that
        # pipeline.spec builds next to the main app .exe.
        folder = Path(sys.executable).resolve().parent
        exe_name = "Pipeline-mcp.exe" if sys.platform == "win32" else "Pipeline-mcp"
        return {"command": str(folder / exe_name), "args": [], "cwd": str(folder)}
    # Dev: use the current interpreter to run the management command.
    return {"command": sys.executable, "args": ["manage.py", "runmcp"], "cwd": str(base_dir)}


def connect(base_dir: Path, frozen: bool, *, config_path: Path | None = None,
            name: str = SERVER_NAME) -> str:
    """Merge the server entry into Claude Desktop's config.

    Returns one of: 'connected' (newly added), 'updated' (changed to match this
    install), 'unchanged' (already correct), 'no-claude' (couldn't find or create
    Claude's config folder), or 'error: <reason>'. Never raises. Preserves all
    other config keys, and refuses to overwrite a config file it can't parse.

    Robustness note — why there is no "does the folder exist?" pre-check:
    the packaged .exe was seen to report 'no-claude' for a %APPDATA%\\Claude
    folder that genuinely exists and is writable. A read-only existence probe
    (os.path.exists / is_dir) intermittently returned False (or raised a
    PermissionError that got swallowed) inside the frozen process, even though a
    normal process saw the folder fine — and that false negative silently
    blocked the write from ever being attempted, leaving users unconnected with
    no manual recourse. So the WRITE itself is now the authoritative test: we
    read+merge, then ensure the directory and write. If Claude Desktop's folder
    is there we write into it; if it isn't, we create it (harmless — Claude
    reads the file when it first launches). Only a write that actually fails is
    reported. The write retries on a transient PermissionError, since Claude
    Desktop/Cowork can briefly hold the file open at startup.
    """
    import time

    try:
        cfg_path = config_path or claude_config_path()
        if not cfg_path:
            return "error: could not determine OS for Claude config path"

        cfg = {}
        if cfg_path.exists():
            try:
                raw = cfg_path.read_text(encoding="utf-8")
                cfg = json.loads(raw) if raw.strip() else {}
            except (json.JSONDecodeError, OSError) as exc:
                # Don't clobber a file we can't understand.
                return f"error: existing Claude config could not be read ({exc})"
            if not isinstance(cfg, dict):
                return "error: existing Claude config is not an object"

        servers = cfg.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            return "error: existing mcpServers is not an object"

        desired = server_entry(base_dir, frozen)
        if servers.get(name) == desired:
            return "unchanged"

        status = "updated" if name in servers else "connected"
        servers[name] = desired

        payload = json.dumps(cfg, indent=2)
        last_exc = None
        for attempt in range(3):
            try:
                cfg_path.parent.mkdir(parents=True, exist_ok=True)
                cfg_path.write_text(payload, encoding="utf-8")
                return status
            except (PermissionError, OSError) as exc:
                last_exc = exc
                time.sleep(0.3 * (attempt + 1))
        # The folder genuinely couldn't be created or written after retries —
        # Claude Desktop most likely isn't installed on this machine at all.
        # 'no-claude' (not 'error') keeps the background watcher retrying, so it
        # connects the moment Claude Desktop is installed/opened, no relaunch.
        return f"no-claude: {cfg_path.parent} could not be written ({last_exc})"
    except Exception as exc:  # noqa: BLE001 — must never break app startup
        return f"error: {type(exc).__name__}: {exc}"
