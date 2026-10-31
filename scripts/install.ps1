# PetroLúmen Windows Setup / Installer
# Installs PetroLúmen to %LOCALAPPDATA%\Programs\PetroLumen
# Creates Desktop & Start Menu shortcuts

param (
    [string]$TargetDir = "$env:LOCALAPPDATA\Programs\PetroLumen"
)

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  PetroLúmen v1.0.0 Windows Installer" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

$SourceRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$DistSource = Join-Path $SourceRoot "dist"

if (-not (Test-Path $DistSource)) {
    Write-Host "[ERROR] 'dist' folder not found. Please run 'npm run build' first." -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Preparing installation directory: $TargetDir" -ForegroundColor Yellow
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

Write-Host "[2/4] Copying application assets..." -ForegroundColor Yellow
$TargetDist = Join-Path $TargetDir "dist"
$TargetScripts = Join-Path $TargetDir "scripts"

if (Test-Path $TargetDist) { Remove-Item $TargetDist -Recurse -Force }
if (Test-Path $TargetScripts) { Remove-Item $TargetScripts -Recurse -Force }

Copy-Item -Path $DistSource -Destination $TargetDist -Recurse -Force
Copy-Item -Path (Join-Path $SourceRoot "scripts") -Destination $TargetScripts -Recurse -Force
Copy-Item -Path (Join-Path $SourceRoot "PetroLumen.cmd") -Destination $TargetDir -Force

# Create Uninstaller script inside TargetDir
$UninstallScriptPath = Join-Path $TargetDir "uninstall.ps1"
$UninstallScriptContent = @"
# PetroLúmen Uninstaller
`$InstallDir = "$TargetDir"
`$DesktopLnk = [System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'PetroLúmen.lnk')
`$StartMenuFolder = [System.IO.Path]::Combine([Environment]::GetFolderPath('Programs'), 'PetroLúmen')

Write-Host "Removendo atalhos do PetroLúmen..." -ForegroundColor Yellow
if (Test-Path `$DesktopLnk) { Remove-Item `$DesktopLnk -Force }
if (Test-Path `$StartMenuFolder) { Remove-Item `$StartMenuFolder -Recurse -Force }

Write-Host "Removendo arquivos do aplicativo..." -ForegroundColor Yellow
if (Test-Path `$InstallDir) {
    # Remove all except uninstall script itself, then schedule self-delete
    Get-ChildItem `$InstallDir -Exclude "uninstall.bat","uninstall.ps1" | Remove-Item -Recurse -Force
    Start-Process cmd.exe -ArgumentList "/c timeout /t 1 >nul & rmdir /s /q `"`$InstallDir`"" -WindowStyle Hidden
}

Write-Host "PetroLúmen foi desinstalado com sucesso." -ForegroundColor Green
"@
Set-Content -Path $UninstallScriptPath -Value $UninstallScriptContent

$UninstallBatPath = Join-Path $TargetDir "uninstall.bat"
$UninstallBatContent = @"
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"
"@
Set-Content -Path $UninstallBatPath -Value $UninstallBatContent

Write-Host "[3/4] Creating Desktop shortcut..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$DesktopShortcutPath = Join-Path $DesktopPath "PetroLúmen.lnk"
$Shortcut = $WshShell.CreateShortcut($DesktopShortcutPath)
$Shortcut.TargetPath = Join-Path $TargetDir "PetroLumen.cmd"
$Shortcut.WorkingDirectory = $TargetDir
$Shortcut.Description = "PetroLúmen - Plataforma de Engenharia de Petróleo"
$Shortcut.Save()

Write-Host "[4/4] Creating Start Menu shortcuts..." -ForegroundColor Yellow
$ProgramsFolder = [Environment]::GetFolderPath("Programs")
$AppMenuFolder = Join-Path $ProgramsFolder "PetroLúmen"
if (-not (Test-Path $AppMenuFolder)) {
    New-Item -ItemType Directory -Path $AppMenuFolder -Force | Out-Null
}

$StartMenuShortcut = $WshShell.CreateShortcut((Join-Path $AppMenuFolder "PetroLúmen.lnk"))
$StartMenuShortcut.TargetPath = Join-Path $TargetDir "PetroLumen.cmd"
$StartMenuShortcut.WorkingDirectory = $TargetDir
$StartMenuShortcut.Description = "PetroLúmen - Plataforma de Engenharia de Petróleo"
$StartMenuShortcut.Save()

$UninstallShortcut = $WshShell.CreateShortcut((Join-Path $AppMenuFolder "Desinstalar PetroLúmen.lnk"))
$UninstallShortcut.TargetPath = (Join-Path $TargetDir "uninstall.bat")
$UninstallShortcut.WorkingDirectory = $TargetDir
$UninstallShortcut.Description = "Desinstalar PetroLúmen"
$UninstallShortcut.Save()

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  Instalação concluída com sucesso!" -ForegroundColor Green
Write-Host "  Atalho criado na sua Área de Trabalho e Menu Iniciar." -ForegroundColor Gray
Write-Host "  Diretório: $TargetDir" -ForegroundColor Gray
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""
