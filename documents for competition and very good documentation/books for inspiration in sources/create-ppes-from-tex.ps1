# create-ppes-from-tex.ps1
#
# Extracts every `\chapter{\code{FILE}}` + `\begin{lstlisting}...\end{lstlisting}`
# block from the PPES .tex document and writes each to a BOM-free file
# under ./ppes-from-tex/.
#
# Usage:
#   .\create-ppes-from-tex.ps1          # faithful extraction
#   .\create-ppes-from-tex.ps1 -Fix     # extract + rewrite pyproject.toml
#                                       # with a working setuptools backend

param([switch]$Fix)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# 1. Locate the .tex source (handles the `~` short-name and case variants)
# ---------------------------------------------------------------------------
$texPath = $null
foreach ($cand in @("BOYUNG~2.TEX","BOYUNG~2.tex","BOYUNG2.TEX","BOYUNG2.tex")) {
    if (Test-Path -LiteralPath $cand) {
        $texPath = (Resolve-Path -LiteralPath $cand).Path
        break
    }
}
if (-not $texPath) {
    $found = Get-ChildItem -File | Where-Object {
        $_.Name -like "*BOYUNG*2*" -and $_.Extension -ieq ".tex"
    } | Select-Object -First 1
    if ($found) { $texPath = $found.FullName }
}
if (-not $texPath) {
    throw "Could not locate the PPES .tex file (BOYUNG~2.TEX) in the current directory."
}
Write-Host "Reading: $texPath" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# 2. Read the file (BOM-tolerant read)
# ---------------------------------------------------------------------------
$tex = [System.IO.File]::ReadAllText($texPath)

# ---------------------------------------------------------------------------
# 3. Extract every \chapter{\code{PATH}} followed by a lstlisting block
# ---------------------------------------------------------------------------
$pattern = '\\chapter\{\\code\{([^}]+)\}\}\s*\r?\n\\begin\{lstlisting\}(\[[^\]]*\])?\r?\n(.*?)\\end\{lstlisting\}'
$matches = [regex]::Matches(
    $tex,
    $pattern,
    [System.Text.RegularExpressions.RegexOptions]::Singleline
)
Write-Host "Found $($matches.Count) file blocks" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# 4. Write each block to disk, BOM-free
# ---------------------------------------------------------------------------
$root    = Join-Path (Get-Location) "ppes-from-tex"
$bomless = New-Object System.Text.UTF8Encoding $false
$written = @()

foreach ($m in $matches) {
    $relPath = $m.Groups[1].Value `
        -replace '\\_','_' `
        -replace '\\%','%' `
        -replace '\\&','&' `
        -replace '\\#','#'

    $content = $m.Groups[3].Value
    $full    = Join-Path $root $relPath
    $dir     = Split-Path $full -Parent

    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($full, $content, $bomless)
    Write-Host "  + $relPath" -ForegroundColor Green
    $written += $relPath
}

# ---------------------------------------------------------------------------
# 5. Optional: apply the pyproject.toml backend fix
# ---------------------------------------------------------------------------
if ($Fix) {
    $pyprojectPath = Join-Path $root "pyproject.toml"
    if (Test-Path -LiteralPath $pyprojectPath) {
        $fixed = @'
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ppes"
version = "1.0.0"
description = "Petroleum Production Engineering Software (Guo 2007)"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [{name = "Engineering Software Planning"}]
dependencies = [
    "numpy>=1.26", "scipy>=1.11", "pandas>=2.1",
    "pydantic>=2.5", "matplotlib>=3.8", "typer>=0.9",
    "openpyxl>=3.1", "reportlab>=4.0", "python-docx>=1.1",
    "sqlalchemy>=2.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.4", "pytest-regressions>=2.5",
       "hypothesis>=6.98", "ruff", "mypy"]
ui  = ["streamlit>=1.30"]
api = ["fastapi>=0.109", "uvicorn[standard]>=0.27"]

[project.scripts]
ppes = "ppes.cli:app"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
ppes = ["data/*.csv"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
'@
        [System.IO.File]::WriteAllText($pyprojectPath, $fixed, $bomless)
        Write-Host "  FIXED: pyproject.toml (setuptools backend + sqlalchemy)" -ForegroundColor Magenta
    }
}

# ---------------------------------------------------------------------------
# 6. Summary + warnings
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " Wrote $($written.Count) files to $root" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Known issues IN THE SOURCE .TEX (not introduced by this script):" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. pyproject.toml declares hatchling as backend but configures" -ForegroundColor Yellow
Write-Host "     [tool.setuptools.*] tables. pip install will fail." -ForegroundColor Yellow
Write-Host "     -> re-run with -Fix to correct this automatically" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. sqlalchemy is not in dependencies, so src/ppes/db.py fails to import." -ForegroundColor Yellow
Write-Host "     -> -Fix adds it" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. Five tests in tests/test_book_examples.py will FAIL because" -ForegroundColor Yellow
Write-Host "     the book's printed answers differ from what the formulas" -ForegroundColor Yellow
Write-Host "     actually produce (the book has arithmetic typos):" -ForegroundColor Yellow
Write-Host "       - test_ex_2_1        mu_o formula gives ~1.665, book prints 1.4819" -ForegroundColor Yellow
Write-Host "       - test_ex_12_1_speed speed_limit gives ~17.6,  book prints 22" -ForegroundColor Yellow
Write-Host "       - test_ex_16_1       beta gives 0.2057,       book prints 0.21 (2.05%)" -ForegroundColor Yellow
Write-Host "       - test_ex_16_2       rate gives 1.34,         book prints 1.04" -ForegroundColor Yellow
Write-Host "       - test_ex_17_1       p_bd gives 6487,         book prints 6600" -ForegroundColor Yellow
Write-Host "     -> Not fixed by this script; these are the .tex's own numbers" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  cd ppes-from-tex"
Write-Host "  python -m venv .venv"
Write-Host "  .venv\Scripts\Activate.ps1"
Write-Host "  pip install -e `".[dev]`""
Write-Host "  pytest -v     # expect 15 passing, 5 failing (see item 3 above)"
Write-Host ""