param([switch]$CreateVenv)

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $scriptDir

if (Test-Path ".venv") { . .\.venv\Scripts\Activate.ps1 } elseif ($CreateVenv) { python -m venv .venv; . .\.venv\Scripts\Activate.ps1; pip install -r ..\requirements.txt }

Write-Host "Running Driller Method Simulation..."
python driller_sim.py
