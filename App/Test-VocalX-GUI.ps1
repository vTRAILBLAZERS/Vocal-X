$ErrorActionPreference='Stop'
$Results=[System.Collections.Generic.List[string]]::new()
$Failed=$false
try {
 $Root=Split-Path $PSScriptRoot -Parent
 $Py=Join-Path $Root '.venv\Scripts\python.exe'
 $Logs=Join-Path $Root ('Temp\GuiCheck-'+[guid]::NewGuid().ToString('N'))
 New-Item -ItemType Directory -Force -Path $Logs | Out-Null
 foreach($Name in @('test_gui_branding.py','test_anyenhance_full.py')){
  $Out=Join-Path $Logs ($Name+'.stdout.txt');$Err=Join-Path $Logs ($Name+'.stderr.txt')
  $Process=Start-Process -FilePath $Py -ArgumentList @('-X','utf8',('"'+(Join-Path $PSScriptRoot $Name)+'"')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $Out -RedirectStandardError $Err
  $Results.Add("$Name Exitcode: $($Process.ExitCode)")
  $Results.Add((Get-Content $Out -Raw -Encoding UTF8));$Results.Add((Get-Content $Err -Raw -Encoding UTF8))
  if($Process.ExitCode -ne 0){throw "$Name fehlgeschlagen"}
 }
 $Results.Add("Logs: $Logs")
 $Results.Add('Sprachen: Deutsch / English; Sprache wird gespeichert.')
 $Results.Add('Entf entfernt Warteschlangeneintraege; keine Audiodateien.')
} catch {$Failed=$true;$Results.Add("FEHLER: $($_.Exception.Message)")}
finally {
 Write-Host "`n############################################################"
 Write-Host 'KOPIERBLOCK FÜR CHATGPT - AB HIER KOPIEREN'
 Write-Host '=== VOCAL X GUI UPDATE ==='
 $Results | ForEach-Object {Write-Host $_}
 Write-Host "Gesamtstatus: $(if($Failed){'FEHLER'}else{'PASS'})"
 Write-Host 'KOPIERBLOCK ENDE'
 Write-Host '############################################################'
}
