param([string]$AudioFile = '', [string]$Preset = 'Clean Acapella')
$ErrorActionPreference = 'Stop'
$Results = [System.Collections.Generic.List[string]]::new()
$Root = Split-Path $PSScriptRoot -Parent
$Py = Join-Path $Root '.venv\Scripts\python.exe'
function Invoke-Check {
    param([string]$Name, [string[]]$Arguments)
    $OutFile = Join-Path $env:TEMP ([guid]::NewGuid().ToString() + '.out')
    $ErrFile = $OutFile + '.err'
    $Quoted = ($Arguments | ForEach-Object { '"' + $_ + '"' }) -join ' '
    $Process = Start-Process -FilePath $Py -ArgumentList $Quoted -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $OutFile -RedirectStandardError $ErrFile
    $Results.Add("$Name exit=$($Process.ExitCode)")
    $Results.Add((Get-Content -LiteralPath $OutFile -Raw -ErrorAction SilentlyContinue))
    $Results.Add((Get-Content -LiteralPath $ErrFile -Raw -ErrorAction SilentlyContinue))
    if ($Process.ExitCode -ne 0) { throw "$Name fehlgeschlagen" }
}
try {
    $Results.Add("Python: $Py")
    Invoke-Check 'Modelle und Presets' @((Join-Path $PSScriptRoot 'pipeline.py'), 'check')
    Invoke-Check 'Lokale Tests' @((Join-Path $PSScriptRoot 'test_pipeline.py'))
    if ($AudioFile) {
        Invoke-Check 'Audio-Pipeline' @((Join-Path $PSScriptRoot 'pipeline.py'), 'run', '--preset', $Preset, '--input', $AudioFile)
    } else { $Results.Add('Audio-Pipeline: nicht angefordert; -AudioFile angeben.') }
} catch {
    $Results.Add("FEHLER: $($_.Exception.Message)")
} finally {
    Write-Host "`n############################################################"
    Write-Host 'KOPIERBLOCK FÜR CHATGPT - AB HIER KOPIEREN'
    Write-Host '=== VOCAL AI PIPELINE ENGINE V1 ==='
    $Results | ForEach-Object { Write-Host $_ }
    Write-Host 'KOPIERBLOCK ENDE'
    Write-Host '############################################################'
}
