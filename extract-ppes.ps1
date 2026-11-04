# extract-ppes.ps1
param([switch]$DryRun)
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath "BOYUNG~2.TEX")) {
    throw "BOYUNG~2.TEX not found in $(Get-Location)"
}
$tex = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath "BOYUNG~2.TEX").Path)

$pat = '(?ms)^\\chapter\{\\code\{([^}]+)\}\}\s*\r?\n\\begin\{lstlisting\}(?:\[[^\]]*\])?\r?\n(.*?)^\\end\{lstlisting\}'
$ms  = [regex]::Matches($tex, $pat)
Write-Host "Found $($ms.Count) file blocks in BOYUNG~2.TEX" -ForegroundColor Cyan

$root = Join-Path (Get-Location) "ppes-extracted"
$utf8 = New-Object System.Text.UTF8Encoding $false
$count = 0

foreach ($m in $ms) {
    $path = $m.Groups[1].Value `
        -replace '\\_','_' -replace '\\%','%' `
        -replace '\\&','&' -replace '\\#','#'
    $path = $path -replace '/', '\'
    $content = $m.Groups[2].Value
    $full = Join-Path $root $path
    $dir  = Split-Path $full -Parent

    if ($DryRun) {
        Write-Host "  [DRY] $path" -ForegroundColor Yellow
    } else {
        if (-not (Test-Path -LiteralPath $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        [System.IO.File]::WriteAllText($full, $content, $utf8)
        Write-Host "  + $path" -ForegroundColor Green
    }
    $count++
}

Write-Host ""
Write-Host "$count files $($DryRun ? 'would be ' : '')written to $root" -ForegroundColor Cyan