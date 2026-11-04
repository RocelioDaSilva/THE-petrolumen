#Requires -Version 5.1
<#
.SYNOPSIS
    Regenerates TREE.md from the current filesystem.
.DESCRIPTION
    Walks the repository, excludes node_modules/.git/caches, writes
    a markdown tree to TREE.md. Idempotent and safe to run anytime.
#>
[CmdletBinding()]
param(
    [string]$OutputPath = "TREE.md",
    [string]$RootPath = ".",
    [string[]]$ExcludeDirs = @(
        "node_modules", ".git", "__pycache__", ".venv", "venv",
        "dist", "build", ".next", "coverage",
        ".pytest_cache", ".mypy_cache", ".ruff_cache",
        ".eggs", ".tox"
    )
)

function Test-Excluded {
    param([string]$Name)
    foreach ($pat in $ExcludeDirs) {
        if ($Name -like $pat -or $Name -like "$pat.*") { return $true }
    }
    return $false
}

function Get-TreeLines {
    param([string]$Path, [int]$Depth = 0, [int]$MaxDepth = 12)
    if ($Depth -gt $MaxDepth) { return }
    $items = Get-ChildItem -Path $Path -Force -ErrorAction SilentlyContinue |
        Where-Object { -not (Test-Excluded $_.Name) } |
        Sort-Object @{Expression={-not $_.PSIsContainer}}, Name
    $count = $items.Count
    $i = 0
    foreach ($item in $items) {
        $i++
        $isLast = ($i -eq $count)
        $connector = if ($isLast) { "`u{2514}`u{2500}`u{2500} " } else { "`u{251C}`u{2500}`u{2500} " }
        $indent = "    " * $Depth
        $suffix = if ($item.PSIsContainer) { "/" } else { "" }
        Write-Output "$indent$connector$($item.Name)$suffix"
        if ($item.PSIsContainer) {
            Get-TreeLines -Path $item.FullName -Depth ($Depth + 1) -MaxDepth $MaxDepth
        }
    }
}

$resolvedRoot = (Resolve-Path $RootPath).Path
$rootName = Split-Path -Leaf $resolvedRoot
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$treeLines = @(Get-TreeLines -Path $resolvedRoot)

$allFiles = Get-ChildItem -Path $resolvedRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $rel = $_.FullName.Substring($resolvedRoot.Length + 1)
        $parts = $rel -split [regex]::Escape([IO.Path]::DirectorySeparatorChar)
        foreach ($p in $parts) { if (Test-Excluded $p) { return $false } }
        return $true
    }

$pyCount = ($allFiles | Where-Object { $_.Extension -eq ".py" }).Count
$totalBytes = ($allFiles | Measure-Object Length -Sum).Sum
if (-not $totalBytes) { $totalBytes = 0 }

$output = @(
    "# Repository Tree",
    "",
    "> **Auto-generated.** Do not edit by hand.",
    "> Run ``npm run tree`` or ``.\tools\Update-Tree.ps1`` to refresh.",
    "",
    "| Field | Value |",
    "|-------|-------|",
    "| Generated | ``$timestamp`` |",
    "| Root | ``$rootName`` |",
    "| Total files | $($allFiles.Count) |",
    "| Python files | $pyCount |",
    "| Total size | $([math]::Round($totalBytes / 1024, 1)) KB |",
    "",
    "## Structure",
    "",
    '```',
    "$rootName/",
    $treeLines,
    '```',
    ""
)

Set-Content -Path $OutputPath -Value ($output -join "`n") -Encoding UTF8 -NoNewline
Write-Host "[update-tree] $OutputPath regenerated: $($allFiles.Count) files, $pyCount Python, $([math]::Round($totalBytes/1024,1)) KB" -ForegroundColor Green