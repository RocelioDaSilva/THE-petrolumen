param(
    [string]$PythonExe = ""
)

Write-Host "Packaging backend with PyInstaller..."

if (-not $PythonExe -or $PythonExe -eq "") {
    if (Test-Path ".venv\Scripts\python.exe") {
        $PythonExe = Join-Path -Path $PWD -ChildPath ".venv\Scripts\python.exe"
        Write-Host "Using virtualenv python: $PythonExe"
    } else {
        $PythonExe = "python"
        Write-Host "Using system python: $PythonExe"
    }
}

# Ensure pip and pyinstaller are available
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install pyinstaller

# Clean previous builds
if (Test-Path "dist") { Remove-Item -Recurse -Force dist }
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "backend.spec") { Remove-Item -Force backend.spec }

# Run PyInstaller
& $PythonExe -m PyInstaller --onefile --name backend backend\main.py

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

# Prepare destination directory inside src-tauri so Tauri can bundle it
$dest = Join-Path -Path "src-tauri" -ChildPath "bundle\resources"
if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Force -Path $dest | Out-Null }

$srcExe = Join-Path -Path "dist" -ChildPath "backend.exe"
if (-not (Test-Path $srcExe)) {
    Write-Error "Expected packaged exe not found: $srcExe"
    exit 1
}

Copy-Item -Path $srcExe -Destination (Join-Path $dest "backend.exe") -Force
Write-Host "Backend packaged and copied to $dest\backend.exe"
