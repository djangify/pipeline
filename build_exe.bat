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
call pipelinevenv\Scripts\activate.bat

:: -----------------------------------------------
:: DEPENDENCIES (app + build tools)
:: -----------------------------------------------
echo  Installing dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check
pip install pyinstaller --quiet --disable-pip-version-check
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
python manage.py collectstatic --noinput >nul 2>&1

:: -----------------------------------------------
:: BUILD
:: -----------------------------------------------
echo  Running PyInstaller...
pyinstaller pipeline.spec --noconfirm
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
echo   Ship the whole dist\Pipeline folder.
echo  =============================================
echo.
pause
