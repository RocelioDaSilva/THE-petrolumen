@echo off
setlocal
title PetroLumen Engineering Platform

cd /d "%~dp0"

echo =======================================================
echo   PetroLumen Petroleum Engineering Platform v1.0.0
echo =======================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0frontend_desktop\desktop_app.py"
    goto finished
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Launching the PyWebView desktop application...
    py -3 "%~dp0frontend_desktop\desktop_app.py"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Desktop startup failed. Install the backend and desktop requirements first.
    )
    goto finished
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Launching the PyWebView desktop application...
    python "%~dp0frontend_desktop\desktop_app.py"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Desktop startup failed. Install Python 3.11+ and the application requirements.
    )
) else (
    echo [ERROR] Python 3.11+ is required. Run scripts\install.ps1 to prepare the desktop application.
)

:finished
pause
