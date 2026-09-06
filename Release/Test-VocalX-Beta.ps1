$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root '.venv\Scripts\python.exe'
$Results = [System.Collections.Generic.List[string]]::new()
$Failures = 0
$LogDir = Join-Path $Root ('Temp\Beta-Check-' + [guid]::NewGuid().ToString('N'))
try {
 New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
 foreach ($Name in @('test_activation.py','test_portability.py','test_license.py','test_pipeline.py','test_restoration.py','test_anyenhance_full.py','test_gui_branding.py','test_qol_core.py','test_qol_gui.py')) {
  $Log = Join-Path $LogDir ($Name + '.log')
  $ErrorActionPreference = 'Continue'
  & $Py -X utf8 (Join-Path $Root ('App\' + $Name)) *> $Log
  $Code = $LASTEXITCODE
  $ErrorActionPreference = 'Stop'
  $Results.Add("$Name : Exitcode $Code")
  if ($Code -ne 0) { $Failures++; $Results.Add((Get-Content -LiteralPath $Log -Tail 25 | Out-String)) }
 }
 $ErrorActionPreference = 'Continue'
 $Status = & $Py -X utf8 (Join-Path $PSScriptRoot 'beta_status.py') 2>&1
 if ($LASTEXITCODE -ne 0) { $Failures++ }
} catch { $Failures++; $Results.Add($_.Exception.Message) }
finally {
 Write-Host '############################################################'
 Write-Host '# KOPIERBLOCK FÜR CHATGPT - AB HIER KOPIEREN'
 Write-Host '############################################################'
 $Status | ForEach-Object { Write-Host $_ }
 Write-Host "Logs: $LogDir"
 $Results | ForEach-Object { Write-Host $_ }
 Write-Host "Tests failed: $Failures"
 Write-Host 'External release ready: NO'
 Write-Host '############################################################'
 Write-Host '# KOPIERBLOCK ENDE'
 Write-Host '############################################################'
}
exit ([int]($Failures -gt 0))
