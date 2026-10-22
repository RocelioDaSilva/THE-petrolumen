param([switch]$CreateVenv)

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $scriptDir

if (Test-Path ".venv") { . .\.venv\Scripts\Activate.ps1 } elseif ($CreateVenv) { python -m venv .venv; . .\.venv\Scripts\Activate.ps1; pip install -r ..\requirements.txt; pip install tensorflow }

Write-Host "Running Production LSTM training (may take time)..."
python train_lstm.py --data data/example_production.csv
