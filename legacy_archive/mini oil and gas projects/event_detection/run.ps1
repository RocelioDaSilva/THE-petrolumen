param([switch]$CreateVenv)

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $scriptDir

if (Test-Path ".venv") { . .\.venv\Scripts\Activate.ps1 } elseif ($CreateVenv) { python -m venv .venv; . .\.venv\Scripts\Activate.ps1; pip install -r ..\requirements.txt }

Write-Host "Running Event Detection..."
python event_detection.py --data data/example_timeseries.csv
