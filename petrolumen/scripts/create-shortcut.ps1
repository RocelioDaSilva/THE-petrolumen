# Cria um atalho na área de trabalho para o executável Tauri
$ProductName = "petrolumen" # Altere se o nome do seu exe for diferente
$ReleaseDir = Join-Path $PSScriptRoot "..\src-tauri\target\release"
$ExePath = Join-Path $ReleaseDir ("$ProductName.exe")

if (!(Test-Path $ExePath)) {
    Write-Error "Executável não encontrado: $ExePath. Rode o build primeiro."
    exit 1
}

$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut((Join-Path $Desktop "$ProductName.lnk"))
$Shortcut.TargetPath = $ExePath
$Shortcut.WorkingDirectory = $ReleaseDir
$Shortcut.WindowStyle = 1
$Shortcut.Description = "Atalho para $ProductName"
$Shortcut.Save()

Write-Host "Atalho criado na área de trabalho para $ExePath"
