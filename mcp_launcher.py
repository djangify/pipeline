"""Console entry point for the Pipeline MCP server (stdio).

Used two ways:
  - Packaged: PyInstaller builds this as Pipeline-mcp.exe (a *console*
    executable -- a windowed .exe has no stdin/stdout, which stdio MCP needs).
    Claude Desktop launches it. See pipeline.spec.
  - Dev:      python mcp_launcher.py   (equivalent to `python manage.py runmcp`)

It reuses the desktop launcher's data-dir + SECRET_KEY handling so the MCP
server reads the SAME database and settings as the app window.

stdout is reserved for the MCP protocol -- nothing here may print to it.
"""
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ.setdefault("DEBUG", "True")

    # Reuse the packaged app's persisted SECRET_KEY / writable data dir so this
    # process points at the same install. Safe no-op in a normal dev checkout.
    try:
        from desktop import _ensure_secret_key, _writable_data_dir

        _ensure_secret_key(_writable_data_dir())
    except Exception:
        pass

    import django

    django.setup()

    # Claude Desktop can start this before the app window has ever run after an
    # update, so apply pending migrations here too (the app does the same on
    # launch). Output goes to a buffer, never stdout, and a failure must not
    # stop the server from starting.
    try:
        import io

        from django.core.management import call_command

        buf = io.StringIO()
        call_command("migrate", interactive=False, verbosity=0, stdout=buf, stderr=buf)
    except Exception as exc:
        print(f"MCP startup migrate failed: {exc}", file=sys.stderr)

    from mcp_server.server import mcp

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
