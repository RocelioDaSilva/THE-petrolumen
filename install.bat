@echo off
setlocal
title Instalador PetroLumen v1.0.0

cd /d "%~dp0"
echo Iniciando o instalador do PetroLumen...
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\install.ps1"

pause
