# extract-ppes.ps1 — PS 5.1, content-based discovery, long-path safe
$ErrorActionPreference = 'Stop'

$srcDir = 'C:\Users\rocel\THE-petrolumen\documents for competition and very good documentation\books for inspiration in sources'
$target = Join-Path $srcDir 'extracted_code'

if (-not (Test-Path -LiteralPath $srcDir)) {
    throw "Source directory not found: $srcDir"
}

# ---------- long-path helper ----------
function Get-LongPath([string]$p) {
    if ([string]::IsNullOrEmpty($p)) { return $p }
    if ($p.StartsWith('\\?\')) { return $p }
    $p = $p -replace '/', '\'
    if ($p -match '^[A-Za-z]:\\') { return '\\?\' + $p }
    return $p
}

# ---------- discover sources ----------
$all = Get-ChildItem -LiteralPath $srcDir -Filter '*.tex' -File
Write-Host ("Found {0} .tex file(s)" -f $all.Count) -ForegroundColor Cyan

$chapters = @()
$sections = @()
foreach ($f in $all) {
    if ($f.Length -eq 0) {
        Write-Host ("  skip (empty): {0}" -f $f.Name) -ForegroundColor DarkGray
        continue
    }
    $long = Get-LongPath $f.FullName
    Write-Host ("  {0}  ({1} bytes, path {2} chars)" -f $f.Name, $f.Length, $long.Length)
    $txt = [System.IO.File]::ReadAllText($long)
    $hasChapter = $txt.Contains('\chapter{\code{')
    $hasSection = $txt.Contains('\section{\code{')
    if ($hasChapter) {
        Write-Host "    -> chapter-source" -ForegroundColor Green
        $chapters += [pscustomobject]@{ Path = $long; Text = $txt; Name = $f.Name }
    } elseif ($hasSection) {
        Write-Host "    -> section-source" -ForegroundColor Green
        $sections += [pscustomobject]@{ Path = $long; Text = $txt; Name = $f.Name }
    } else {
        Write-Host "    -> skip (no code blocks)" -ForegroundColor DarkGray
    }
}

if ($chapters.Count -eq 0 -and $sections.Count -eq 0) {
    throw "No usable source files."
}

# ---------- fresh target ----------
if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
New-Item -ItemType Directory -Path $target -Force | Out-Null
Write-Host "Target: $target" -ForegroundColor Cyan

# ---------- patterns ----------
$chapterPat = '(?ms)^\\chapter\{\\code\{([^}]+)\}\}[^\r\n]*\r?\n\\begin\{lstlisting\}(?:\[[^\]]*\])?\r?\n(.*?)^\\end\{lstlisting\}'
$sectionPat = '(?ms)^\\section\{\\code\{([^}]+)\}\}[^\r\n]*\r?\n\\begin\{lstlisting\}(?:\[[^\]]*\])?\r?\n(.*?)^\\end\{lstlisting\}'

$utf8 = New-Object System.Text.UTF8Encoding $false
$script:written = 0
$script:skipped = 0
$script:failed  = 0

function Process-Source($srcObj, $pat, $isChapter, $label) {
    Write-Host ""
    Write-Host ("=== {0} [{1}] ===" -f $srcObj.Name, $label) -ForegroundColor Cyan
    $ms = [regex]::Matches($srcObj.Text, $pat)
    Write-Host ("  {0} match(es)" -f $ms.Count)
    if ($ms.Count -eq 0) { return }

    foreach ($m in $ms) {
        $rel = $m.Groups[1].Value
        $rel = $rel -replace '\\_','_' -replace '\\%','%' -replace '\\&','&' -replace '\\#','#'
        $rel = $rel.Replace('/','\').Trim()
        $full = Join-Path $target $rel

        if (-not $isChapter -and (Test-Path -LiteralPath $full)) {
            $script:skipped++
            continue
        }

        try {
            $dir = Split-Path $full -Parent
            if ($dir -and -not (Test-Path -LiteralPath $dir)) {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
            }
            $longFull = Get-LongPath $full
            [System.IO.File]::WriteAllText($longFull, $m.Groups[2].Value, $utf8)
            Write-Host ("    + {0}  ({1} bytes)" -f $rel, $m.Groups[2].Value.Length) -ForegroundColor Green
            $script:written++
        } catch {
            Write-Host ("    ! FAILED {0}: {1}" -f $rel, $_.Exception.Message) -ForegroundColor Red
            $script:failed++
        }
    }
}

foreach ($c in $chapters) { Process-Source $c $chapterPat $true  'chapter' }
foreach ($s in $sections) { Process-Source $s $sectionPat $false 'section' }

# ---------- summary ----------
Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host (" Written : {0}" -f $script:written) -ForegroundColor Green
Write-Host (" Skipped : {0}" -f $script:skipped) -ForegroundColor Yellow
Write-Host (" Failed  : {0}" -f $script:failed) -ForegroundColor Red
Write-Host (" Target  : {0}" -f $target) -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

if ($script:written -gt 0) {
    Write-Host ""
    Write-Host "Files written:" -ForegroundColor Cyan
    Get-ChildItem -LiteralPath $target -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($target.Length + 1)
        Write-Host ("  {0,-55} {1,7} bytes" -f $rel, $_.Length)
    }
}