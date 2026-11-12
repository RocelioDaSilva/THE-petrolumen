param(
    [switch]$SkipFrontendBuild,
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $repositoryRoot

try {
    $buildTemp = Join-Path $repositoryRoot ".temp\build-tmp"
    New-Item -ItemType Directory -Force $buildTemp | Out-Null
    $env:TEMP = $buildTemp
    $env:TMP = $buildTemp

    if (-not $SkipDependencyInstall) {
        python -m pip install -e .\backend `
            -r .\frontend_desktop\requirements_desktop.txt `
            -r .\frontend_desktop\requirements_packaging.txt
        if ($LASTEXITCODE -ne 0) {
            throw "Could not install the desktop runtime and packaging dependencies."
        }
    }

    if (-not $SkipFrontendBuild) {
        npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "The React frontend build failed."
        }
    }

    if (-not (Test-Path .\dist\index.html)) {
        throw "The React build is missing at dist\index.html."
    }

    python -m PyInstaller --version
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller is unavailable in the selected Python environment."
    }

    python -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath .\release\desktop `
        --workpath .\.temp\pyinstaller-work `
        .\petrolumen_desktop.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed to create the desktop application."
    }

    Write-Output "Desktop application created at release\desktop\PetroLumen\PetroLumen.exe"
}
finally {
    Pop-Location
}
