@echo off
title Pipeline - Build Desktop App
color 0B

echo.
echo  =============================================
echo   Building Pipeline.exe (desktop app)
echo  =============================================
echo.

:: -----------------------------------------------
:: VIRTUAL ENVIRONMENT
:: -----------------------------------------------
if not exist "pipelinevenv\Scripts\activate.bat" (
    echo  Creating virtual environment...
    python -m venv pipelinevenv
)
:: Call the venv's python directly rather than relying on activate.bat: that
:: script hard-codes the folder the venv was created in, so after the project
:: is moved it silently puts a dead path on PATH and pip/pyinstaller fall
:: through to the system Python instead.
set "PY=pipelinevenv\Scripts\python.exe"

:: -----------------------------------------------
:: DEPENDENCIES (app + build tools)
:: -----------------------------------------------
echo  Installing dependencies...
"%PY%" -m pip install -r requirements.txt --quiet --disable-pip-version-check
"%PY%" -m pip install pyinstaller --quiet --disable-pip-version-check
if errorlevel 1 (
    color 0C
    echo  ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

:: -----------------------------------------------
:: COLLECT STATIC FILES (bundled into the build)
:: -----------------------------------------------
echo  Collecting static files...
"%PY%" manage.py collectstatic --noinput >nul 2>&1

:: -----------------------------------------------
:: BUILD
:: -----------------------------------------------
echo  Running PyInstaller...
"%PY%" -m PyInstaller pipeline.spec --noconfirm
if errorlevel 1 (
    color 0C
    echo  ERROR: Build failed. Re-run after setting console=True in pipeline.spec
    echo  to see the underlying error.
    pause
    exit /b 1
)

echo.
echo  =============================================
echo   Done. Your app is in:  dist\Pipeline\Pipeline.exe
echo   (Pipeline-mcp.exe next to it is the Claude Desktop connector --
echo   launching Pipeline.exe registers it in Claude Desktop automatically.)
echo   Ship the whole dist\Pipeline folder.
echo  =============================================
echo.
pause
