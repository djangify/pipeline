# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Pipeline (desktop build).

Build from the project root, with the virtual environment active:

    pyinstaller pipeline.spec

Output: dist/Pipeline/ with TWO executables:
  - Pipeline.exe      the app window (windowed)
  - Pipeline-mcp.exe  the MCP server for Claude Desktop (console -- stdio
                      needs real stdin/stdout, which a windowed exe lacks)

Ship the whole Pipeline folder. Claude Desktop is pointed at Pipeline-mcp.exe
automatically on launch (see desktop.py / mcp_server/desktop_connect.py).
"""

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

datas = []
binaries = []
hiddenimports = []

# Packages that load templates / static / submodules dynamically and
# therefore need everything bundled (collect_all = data files + binaries +
# submodules).
for pkg in ["django", "adminita", "rest_framework", "whitenoise", "waitress", "webview", "PIL"]:
    p_datas, p_binaries, p_hidden = collect_all(pkg, on_error="ignore")
    datas += p_datas
    binaries += p_binaries
    hiddenimports += p_hidden

# MCP SDK: collect only the server/client/shared subpackages, NOT mcp.cli.
# mcp.cli imports the optional 'typer' dependency and calls sys.exit(1) at
# import time when it's missing, which crashes a whole-package collect_all.
for sub in ["mcp.server", "mcp.client", "mcp.shared"]:
    hiddenimports += collect_submodules(sub)
hiddenimports += ["mcp", "mcp.types"]
datas += collect_data_files("mcp")

# Local Django apps + the project package. Django imports these by name at
# runtime, so PyInstaller can't discover them by following imports alone.
for pkg in ["config", "crm", "research", "mcp_server"]:
    hiddenimports += collect_submodules(pkg)

# Templates. collect_submodules() only gathers Python modules, not data
# files, so each app's own templates/ must be listed explicitly. They land in
# _internal/<app>/templates, where Django's app_directories loader looks.
# A new app with templates needs a line here too, or its pages 500 in the
# .exe while working fine from source.
datas += [
    ("templates", "templates"),
    ("crm/templates", "crm/templates"),
    ("research/templates", "research/templates"),
]

# Modules Pipeline references by string name (in settings: MIDDLEWARE,
# ROOT_URLCONF, included urlconfs). PyInstaller can't see these by following
# imports, so they must be listed explicitly.
hiddenimports += [
    "config.settings",
    "config.urls",
    "config.wsgi",
    "crm.urls",
    "crm.views",
    "crm.apps",
    "crm.serializers",
    "crm.admin",
    "crm.management.commands.runmcp",
    "research.urls",
    "research.api_urls",
    "research.views",
    "research.apps",
    "research.serializers",
    "research.admin",
    "research.management.commands.import_research_db",
    "mcp_server.server",
    "mcp_server.desktop_connect",
    # mcp_launcher.py imports desktop lazily for the shared data dir/SECRET_KEY.
    "desktop",
]

# Lazily-imported bits that the analyzer can miss.
hiddenimports += [
    "environ",
    "PIL",
    "django.contrib.staticfiles",
]


# --- Analysis 1: the app window (entry point desktop.py) -------------------
a_app = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz_app = PYZ(a_app.pure)
exe_app = EXE(
    pyz_app,
    a_app.scripts,
    [],
    exclude_binaries=True,
    name="Pipeline",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # set True temporarily if you need to see error output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# --- Analysis 2: the MCP server (entry point mcp_launcher.py) ---------------
# Console subsystem: MCP stdio needs real stdin/stdout, which a windowed exe
# does not have. Claude Desktop launches this with piped std handles.
a_mcp = Analysis(
    ["mcp_launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz_mcp = PYZ(a_mcp.pure)
exe_mcp = EXE(
    pyz_mcp,
    a_mcp.scripts,
    [],
    exclude_binaries=True,
    name="Pipeline-mcp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Collect both executables and their (deduplicated) dependencies into one
# shippable folder.
coll = COLLECT(
    exe_app,
    exe_mcp,
    a_app.binaries,
    a_app.datas,
    a_mcp.binaries,
    a_mcp.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Pipeline",
)
