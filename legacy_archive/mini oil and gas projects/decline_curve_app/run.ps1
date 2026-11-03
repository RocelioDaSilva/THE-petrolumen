param([switch]$CreateVenv)

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $scriptDir

if (Test-Path ".venv") {
  Write-Host "Activating virtualenv..."
  . .\.venv\Scripts\Activate.ps1
} elseif ($CreateVenv) {
  Write-Host "Creating virtualenv..."
  python -m venv .venv
  . .\.venv\Scripts\Activate.ps1
  pip install -r ..\requirements.txt
} else {
  Write-Host "No .venv found. Create one with: python -m venv .venv; . .\\.venv\\Scripts\\Activate.ps1; pip install -r ..\\requirements.txt"
}

Write-Host "Running Decline Curve App (Streamlit)..."
streamlit run app.py
