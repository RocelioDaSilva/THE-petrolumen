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
$BackendSource = Join-Path $SourceRoot "backend"
$DesktopSource = Join-Path $SourceRoot "frontend_desktop"
$WebSource = Join-Path $SourceRoot "dist"

if (-not (Test-Path (Join-Path $BackendSource "app\main.py")) -or
    -not (Test-Path (Join-Path $DesktopSource "desktop_app.py")) -or
    -not (Test-Path (Join-Path $WebSource "index.html"))) {
    Write-Host "[ERROR] Backend, PyWebView application, or built React app is missing. Run npm run build first." -ForegroundColor Red
    exit 1
}

Write-Host "[1/5] Preparing installation directory: $TargetDir" -ForegroundColor Yellow
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

Write-Host "[2/4] Copying backend and desktop application..." -ForegroundColor Yellow
$TargetBackend = Join-Path $TargetDir "backend"
$TargetDesktop = Join-Path $TargetDir "frontend_desktop"
$TargetWeb = Join-Path $TargetDir "dist"

if (Test-Path $TargetBackend) { Remove-Item $TargetBackend -Recurse -Force }
if (Test-Path $TargetDesktop) { Remove-Item $TargetDesktop -Recurse -Force }
if (Test-Path $TargetWeb) { Remove-Item $TargetWeb -Recurse -Force }

Copy-Item -Path $BackendSource -Destination $TargetBackend -Recurse -Force
Copy-Item -Path $DesktopSource -Destination $TargetDesktop -Recurse -Force
Copy-Item -Path $WebSource -Destination $TargetWeb -Recurse -Force
Copy-Item -Path (Join-Path $SourceRoot "PetroLumen.cmd") -Destination $TargetDir -Force

Write-Host "[3/5] Preparing the Python runtime..." -ForegroundColor Yellow
$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PythonLauncher) {
    $PythonExe = $PythonLauncher.Source
    $PythonArgs = @("-3")
} else {
    $PythonLauncher = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonLauncher) {
        Write-Host "[ERROR] Python 3.11 or newer is required to install the desktop application." -ForegroundColor Red
        exit 1
    }
    $PythonExe = $PythonLauncher.Source
    $PythonArgs = @()
}

$PythonVersionText = & $PythonExe @PythonArgs -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if ($LASTEXITCODE -ne 0 -or [version]$PythonVersionText -lt [version]"3.11") {
    Write-Host "[ERROR] Python 3.11 or newer is required. Detected: $PythonVersionText" -ForegroundColor Red
    exit 1
}

$VenvPath = Join-Path $TargetDir ".venv"
if (Test-Path $VenvPath) { Remove-Item $VenvPath -Recurse -Force }
& $PythonExe @PythonArgs -m venv $VenvPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Could not create the application's Python environment." -ForegroundColor Red
    exit 1
}

$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Could not prepare pip in the application environment." -ForegroundColor Red
    exit 1
}
& $VenvPython -m pip install $TargetBackend
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Could not install the backend dependencies." -ForegroundColor Red
    exit 1
}
& $VenvPython -m pip install -r (Join-Path $TargetDesktop "requirements_desktop.txt")
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Could not install the PyWebView desktop dependencies." -ForegroundColor Red
    exit 1
}

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

Write-Host "[4/5] Creating Desktop shortcut..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$DesktopShortcutPath = Join-Path $DesktopPath "PetroLúmen.lnk"
$Shortcut = $WshShell.CreateShortcut($DesktopShortcutPath)
$Shortcut.TargetPath = Join-Path $TargetDir "PetroLumen.cmd"
$Shortcut.WorkingDirectory = $TargetDir
$Shortcut.Description = "PetroLúmen - Plataforma de Engenharia de Petróleo"
$Shortcut.Save()

Write-Host "[5/5] Creating Start Menu shortcuts..." -ForegroundColor Yellow
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
