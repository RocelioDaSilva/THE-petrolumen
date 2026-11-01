# Starts each project's run.ps1 in a new PowerShell window using Start-Process
$root = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$projects = @(
  'decline_curve_app',
  'nodal_analysis',
  'facies_classification',
  'rop_prediction',
  'well_trajectory_3d',
  'event_detection',
  'driller_method_simulation',
  'drilling_fluids_ecd',
  'petrophysical_analysis',
  'production_lstm',
  'inspection_checklist_streamlit',
  'volve_data_analysis',
  'integrated_dashboard_python'
)

foreach ($proj in $projects) {
  $path = Join-Path $root $proj
  $run = Join-Path $path 'run.ps1'
  if (Test-Path $run) {
    Write-Host "Starting $proj in new window..."
    Start-Process powershell -ArgumentList "-NoExit","-Command","Set-Location -LiteralPath '$path'; .\\run.ps1"
    Start-Sleep -Milliseconds 500
  } else {
    Write-Host "No run.ps1 found for $proj, skipping."
  }
}

Write-Host "All Start-Process calls issued. Close windows when done."