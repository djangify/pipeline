# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Pipeline (desktop build).

Build from the project root, with the virtual environment active:

    pyinstaller pipeline.spec

Output: dist/Pipeline/Pipeline.exe  (a one-folder app -- ship the whole
Pipeline folder)
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

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

# Local Django apps + the project package. Django imports these by name at
# runtime, so PyInstaller can't discover them by following imports alone.
for pkg in ["config", "crm"]:
    hiddenimports += collect_submodules(pkg)

# Templates. collect_submodules() only gathers Python modules, not data
# files, so crm's own templates/ must be listed explicitly. It lands in
# _internal/crm/templates, where Django's app_directories loader looks.
datas += [
    ("templates", "templates"),
    ("crm/templates", "crm/templates"),
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
]

# Lazily-imported bits that the analyzer can miss.
hiddenimports += [
    "environ",
    "PIL",
    "django.contrib.staticfiles",
]


a = Analysis(
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

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
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

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Pipeline",
)
