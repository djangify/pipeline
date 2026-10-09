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
"%PY%" -m pip install pyinstaller==6.22.3 --quiet --disable-pip-version-check
if errorlevel 1 (
    color 0C
    echo  ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

:: -----------------------------------------------
:: BUILD CSS (Tailwind) - compiles static\css\output.css so the .exe ships
:: with current styles. Needs Node.js; without it the existing output.css
:: (committed to the repo) is used as it is.
:: -----------------------------------------------
where npm >nul 2>&1
if errorlevel 1 (
    echo  npm not found - using the existing static\css\output.css.
) else (
    if not exist "node_modules\.bin\tailwindcss.cmd" (
        echo  Installing Node dependencies...
        call npm install --silent
    )
    echo  Building Tailwind CSS...
    call npm run build:css
    if errorlevel 1 (
        color 0C
        echo  ERROR: Tailwind CSS build failed.
        pause
        exit /b 1
    )
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

:: -----------------------------------------------
:: GUIDES, LICENSE AND RESET SCRIPT (shipped next to Pipeline.exe)
:: -----------------------------------------------
copy /Y LICENSE.txt dist\Pipeline\LICENSE.txt >nul
copy /Y Pipeline-Reset-Password.bat dist\Pipeline\Pipeline-Reset-Password.bat >nul
copy /Y docs\HOW-TO-OPEN-PIPELINE.pdf dist\Pipeline\ >nul
copy /Y docs\HOW-TO-OPEN-PIPELINE.txt dist\Pipeline\ >nul
copy /Y docs\Pipeline-Setup-Guide.pdf dist\Pipeline\ >nul
copy /Y docs\Pipeline-Setup-Guide.txt dist\Pipeline\ >nul
copy /Y docs\THIRD_PARTY_NOTICES.pdf dist\Pipeline\ >nul
copy /Y docs\THIRD_PARTY_NOTICES.txt dist\Pipeline\ >nul

echo.
echo  =============================================
echo   Done. Your app is in:  dist\Pipeline\Pipeline.exe
echo   (Pipeline-mcp.exe next to it is the Claude Desktop connector --
echo   launching Pipeline.exe registers it in Claude Desktop automatically.)
echo   Ship the whole dist\Pipeline folder.
echo  =============================================
echo.
pause
