@echo off
title Pipeline - Reset password
echo.
echo  This gives your Pipeline login a NEW random password.
echo  Your contacts and research are not changed.
echo  Close Pipeline first if it is open.
echo.
pause
if exist "%~dp0Pipeline.exe" (
    "%~dp0Pipeline.exe" --reset-password
) else (
    if exist "%~dp0pipelinevenv\Scripts\python.exe" (
        "%~dp0pipelinevenv\Scripts\python.exe" "%~dp0manage.py" create_default_user --reset
    ) else (
        echo  Could not find Pipeline.exe or the pipelinevenv folder next to this file.
    )
)
echo.
echo  The new password is in first_login.txt (it opens in Notepad for the app version).
echo  Log in, click Change password, choose your own, and the file is deleted for you.
pause
