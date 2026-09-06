param([switch]$GPU)
$ErrorActionPreference='Stop'
$Results=[System.Collections.Generic.List[string]]::new()
$Failed=$false
try {
 $Root=Split-Path $PSScriptRoot -Parent
 $Py=Join-Path $Root '.venv\Scripts\python.exe'
 $LogDir=Join-Path $Root ('Temp\FullModelCheck-'+[guid]::NewGuid().ToString('N'))
 New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
 $ModelDir=Join-Path $Root 'Models\AnyEnhance-360M'
 $Manifest=Get-Content (Join-Path $ModelDir 'provenance.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 foreach($Entry in $Manifest.sha256.PSObject.Properties){
  $Actual=(Get-FileHash -LiteralPath (Join-Path $ModelDir $Entry.Name) -Algorithm SHA256).Hash
  if($Actual -ne $Entry.Value){throw ('Pruefsumme falsch: '+$Entry.Name)}
  $Results.Add('SHA256 OK: '+$Entry.Name)
 }
 foreach($Script in @('test_pipeline.py','test_restoration.py','test_anyenhance_full.py')) {
  $Stdout=Join-Path $LogDir ($Script+'.stdout.txt');$Stderr=Join-Path $LogDir ($Script+'.stderr.txt')
  $Process=Start-Process -FilePath $Py -ArgumentList @('-X','utf8',('"'+(Join-Path $PSScriptRoot $Script)+'"')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr
  $Results.Add("$Script Exitcode: $($Process.ExitCode)")
  $Results.Add((Get-Content $Stdout -Raw -Encoding UTF8));$Results.Add((Get-Content $Stderr -Raw -Encoding UTF8))
  if($Process.ExitCode -ne 0){throw "$Script fehlgeschlagen"}
 }
 if($GPU){
  $Stdout=Join-Path $LogDir 'gpu.stdout.txt';$Stderr=Join-Path $LogDir 'gpu.stderr.txt'
  $Process=Start-Process -FilePath $Py -ArgumentList @('-X','utf8',('"'+(Join-Path $PSScriptRoot 'test_anyenhance_full.py')+'"'),'--gpu') -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr
  $Results.Add("GPU Exitcode: $($Process.ExitCode)")
  $Results.Add((Get-Content $Stdout -Raw -Encoding UTF8))
  if($Process.ExitCode -ne 0){$Results.Add((Get-Content $Stderr -Raw -Encoding UTF8));throw 'GPU-Test fehlgeschlagen'}
 }
 $Report=Join-Path $Root 'Temp\AnyEnhance360M-Test\verified-report.json'
 if(Test-Path $Report){$Results.Add('Letzter gespeicherter GPU-Bericht:');$Results.Add((Get-Content $Report -Raw -Encoding UTF8))}
 $Results.Add('Modell: AnyEnhance 360M SelfCritic V2')
 $Results.Add('Presets: AnyEnhance 360M - Isolierte Vocal / AnyEnhance 360M - Song zu Vocal')
 $Results.Add("Logs: $LogDir")
} catch {$Failed=$true;$Results.Add("FEHLER: $($_.Exception.Message)")}
finally {
 Write-Host "`n############################################################"
 Write-Host 'KOPIERBLOCK FÜR CHATGPT - AB HIER KOPIEREN'
 Write-Host '=== ANYENHANCE 360M COMPLETE CHECK ==='
 $Results | ForEach-Object {Write-Host $_}
 Write-Host "Gesamtstatus: $(if($Failed){'FEHLER'}else{'PASS'})"
 Write-Host 'KOPIERBLOCK ENDE'
 Write-Host '############################################################'
}
