#Requires -Version 5.1
<#
.SYNOPSIS
    Watches the repository and regenerates TREE.md on any change.
#>
[CmdletBinding()]
param()

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$updateScript = Join-Path $scriptDir "Update-Tree.ps1"
$repoRoot = Split-Path -Parent $scriptDir

if (-not (Test-Path $updateScript)) {
    Write-Error "Update-Tree.ps1 not found at $updateScript"
    exit 1
}

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $repoRoot
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true
$watcher.NotifyFilter = ([System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::DirectoryName -bor [System.IO.NotifyFilters]::LastWrite)

$script:lastRun = [DateTime]::MinValue
$script:cooldownSec = 2

$action = {
    $now = Get-Date
    if (($now - $script:lastRun).TotalSeconds -lt $script:cooldownSec) { return }
    $script:lastRun = $now
    try { & $updateScript } catch { Write-Warning "[watch-tree] Update failed: $_" }
}

$subs = @()
$subs += Register-ObjectEvent -InputObject $watcher -EventName Changed -Action $action
$subs += Register-ObjectEvent -InputObject $watcher -EventName Created -Action $action
$subs += Register-ObjectEvent -InputObject $watcher -EventName Deleted -Action $action
$subs += Register-ObjectEvent -InputObject $watcher -EventName Renamed -Action $action

Write-Host "[watch-tree] Watching $repoRoot. Ctrl+C to stop." -ForegroundColor Cyan
try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    $watcher.EnableRaisingEvents = $false
    $subs | ForEach-Object { Unregister-Event -SourceIdentifier $_.Name -ErrorAction SilentlyContinue }
    Write-Host "[watch-tree] Stopped." -ForegroundColor Yellow
}