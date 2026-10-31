# PetroLúmen Native Windows HTTP Server
# Pure PowerShell using .NET HttpListener - runs on any standard Windows 10/11 machine without Node.js

param (
    [int]$Port = 3000,
    [string]$DistPath = ""
)

if ([string]::IsNullOrWhiteSpace($DistPath)) {
    $DistPath = Join-Path $PSScriptRoot "..\dist"
}
$DistPath = [System.IO.Path]::GetFullPath($DistPath)

if (-not (Test-Path $DistPath)) {
    Write-Error "Distribution directory not found at: $DistPath"
    exit 1
}

$MimeTypes = @{
    ".html" = "text/html; charset=utf-8"
    ".js"   = "application/javascript; charset=utf-8"
    ".mjs"  = "application/javascript; charset=utf-8"
    ".css"  = "text/css; charset=utf-8"
    ".json" = "application/json; charset=utf-8"
    ".png"  = "image/png"
    ".jpg"  = "image/jpeg"
    ".jpeg" = "image/jpeg"
    ".gif"  = "image/gif"
    ".svg"  = "image/svg+xml"
    ".ico"  = "image/x-icon"
    ".pdf"  = "application/pdf"
    ".wasm" = "application/wasm"
    ".woff" = "font/woff"
    ".woff2"= "font/woff2"
    ".ttf"  = "font/ttf"
    ".txt"  = "text/plain; charset=utf-8"
}

$Listener = New-Object System.Net.HttpListener
$Prefix = "http://localhost:$Port/"
$Listener.Prefixes.Add($Prefix)

try {
    $Listener.Start()
} catch {
    # If port 3000 is occupied, pick an alternate port
    $Port = 3005
    $Prefix = "http://localhost:$Port/"
    $Listener = New-Object System.Net.HttpListener
    $Listener.Prefixes.Add($Prefix)
    $Listener.Start()
}

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  PetroLúmen Engineering Platform (v1.0.0)" -ForegroundColor Green
Write-Host "  Serving from: $DistPath" -ForegroundColor Gray
Write-Host "  Listening on: $Prefix" -ForegroundColor Yellow
Write-Host "  Press Ctrl+C to stop the server." -ForegroundColor Gray
Write-Host "=======================================================" -ForegroundColor Cyan

# Open in browser / app mode
$AppUrl = $Prefix
$EdgePaths = @(
    "$env:ProgramFiles (x86)\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
)
$FoundEdge = $false
foreach ($p in $EdgePaths) {
    if (Test-Path $p) {
        Start-Process $p -ArgumentList "--app=$AppUrl"
        $FoundEdge = $true
        break
    }
}
if (-not $FoundEdge) {
    Start-Process $AppUrl
}

try {
    while ($Listener.IsListening) {
        $Context = $Listener.GetContext()
        $Request = $Context.Request
        $Response = $Context.Response

        $RawPath = $Request.Url.LocalPath.TrimStart('/')
        if ([string]::IsNullOrWhiteSpace($RawPath)) {
            $RawPath = "index.html"
        }
        $TargetFile = Join-Path $DistPath ([System.Uri]::UnescapeDataString($RawPath))

        if (-not (Test-Path $TargetFile -PathType Leaf)) {
            # SPA Fallback
            $TargetFile = Join-Path $DistPath "index.html"
        }

        $Ext = [System.IO.Path]::GetExtension($TargetFile).ToLower()
        $ContentType = if ($MimeTypes.ContainsKey($Ext)) { $MimeTypes[$Ext] } else { "application/octet-stream" }

        try {
            $Bytes = [System.IO.File]::ReadAllBytes($TargetFile)
            $Response.ContentType = $ContentType
            $Response.ContentLength64 = $Bytes.Length
            $Response.AddHeader("Access-Control-Allow-Origin", "*")
            $Response.AddHeader("X-Content-Type-Options", "nosniff")
            $Response.StatusCode = 200
            $Response.OutputStream.Write($Bytes, 0, $Bytes.Length)
        } catch {
            $Response.StatusCode = 500
        } finally {
            $Response.Close()
        }
    }
} finally {
    $Listener.Stop()
    $Listener.Close()
}
