@echo off
setlocal
title PetroLumen Engineering Platform

cd /d "%~dp0"

echo =======================================================
echo   PetroLumen Petroleum Engineering Platform v1.0.0
echo =======================================================
echo.

where node >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Node.js detected. Launching high-performance server...
    start "" http://localhost:3000
    node scripts\server.cjs
) else (
    echo [INFO] Launching native Windows server via PowerShell...
    powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\serve.ps1"
)

pause
