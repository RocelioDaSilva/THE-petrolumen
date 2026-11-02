# Script de build automatizado para Windows
# Mais robusto: usa caminhos relativos ao script, tratamento de erros e restaura diretório
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir = Resolve-Path "$ScriptDir\.."
$AppDir = Join-Path $RootDir "app"
$BackendDir = Join-Path $RootDir "backend"
$TauriDir = Join-Path $RootDir "src-tauri"
$OrigDir = Get-Location

try {
    Write-Host "[1/5] Instalando dependências do frontend..."
    Set-Location $AppDir
    if (Test-Path package-lock.json) {
        npm install
        if (!$?) { Write-Error 'Falha ao instalar dependências do frontend.'; exit 1 }
    } elseif (Test-Path yarn.lock) {
        yarn install
        if (!$?) { Write-Error 'Falha ao instalar dependências do frontend (yarn).' ; exit 1 }
    } elseif (Test-Path pnpm-lock.yaml) {
        pnpm install
        if (!$?) { Write-Error 'Falha ao instalar dependências do frontend (pnpm).' ; exit 1 }
    } else {
        npm install
        if (!$?) { Write-Error 'Falha ao instalar dependências do frontend.'; exit 1 }
    }
    Write-Host "Dependências do frontend instaladas."

    Write-Host "[2/5] Instalando dependências do backend Python..."
    Set-Location $BackendDir
    if (Test-Path requirements.txt) {
        pip install -r requirements.txt
        if (!$?) { Write-Error 'Falha ao instalar dependências do backend.'; exit 1 }
    } else {
        Write-Host "Nenhum requirements.txt encontrado. Pulando backend."
    }
    Write-Host "Dependências do backend instaladas."

    Write-Host "[3/5] Build do frontend..."
    Set-Location $AppDir
    npm run build
    if (!$?) { Write-Error 'Falha no build do frontend.'; exit 1 }
    Write-Host "Build do frontend concluído."

    Write-Host "[4/5] Build do Tauri..."
    Set-Location $TauriDir
    if (Test-Path .tauri) {
        Remove-Item .tauri -Recurse -Force
    }
    tauri build
    if (!$?) { Write-Error 'Falha no build do Tauri.'; exit 1 }
    Write-Host "Build do Tauri concluído."

    Write-Host "[5/5] Processo de build finalizado com sucesso!"

    # Cria atalho na área de trabalho para o executável Tauri
    $ProductName = "petrolumen" # Altere se o nome do seu exe for diferente
    $ReleaseDir = Join-Path $TauriDir "target\release"
    $ExePath = Join-Path $ReleaseDir ("$ProductName.exe")
    if (Test-Path $ExePath) {
        $WshShell = New-Object -ComObject WScript.Shell
        $Desktop = [Environment]::GetFolderPath("Desktop")
        $Shortcut = $WshShell.CreateShortcut((Join-Path $Desktop "$ProductName.lnk"))
        $Shortcut.TargetPath = $ExePath
        $Shortcut.WorkingDirectory = $ReleaseDir
        $Shortcut.WindowStyle = 1
        $Shortcut.Description = "Atalho para $ProductName"
        $Shortcut.Save()
        Write-Host "Atalho criado na área de trabalho para $ExePath"
    } else {
        Write-Host "Executável não encontrado para criar atalho: $ExePath"
    }
} catch {
    Write-Error "Erro durante o processo de build: $_"
    exit 1
} finally {
    Set-Location $OrigDir
}
