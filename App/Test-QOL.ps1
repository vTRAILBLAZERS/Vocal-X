$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root '.venv\Scripts\python.exe'
$Report = [System.Collections.Generic.List[string]]::new()
$LogDir = Join-Path $Root ('Temp\QOL-Check-' + [guid]::NewGuid().ToString('N'))
$Failed = 0
try {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    if (-not (Test-Path -LiteralPath $Py)) { throw "Python fehlt: $Py" }
    foreach ($Test in @('test_pipeline.py','test_restoration.py','test_anyenhance_full.py','test_gui_branding.py','test_qol_core.py','test_qol_gui.py')) {
        $Log = Join-Path $LogDir ($Test + '.log')
        $ErrorActionPreference = "Continue"
        & $Py (Join-Path $PSScriptRoot $Test) *> $Log
        $ErrorActionPreference = "Stop"
        $Code = $LASTEXITCODE
        $Report.Add("$Test : Exitcode $Code")
        if ($Code -ne 0) { $Failed++; $Report.Add((Get-Content -LiteralPath $Log -Tail 35 | Out-String)) }
    }
    $ErrorActionPreference = "Continue"
    $Hardware = 'import torch; print("CUDA:", torch.cuda.is_available()); print("Runtime:", torch.version.cuda); print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "keine"); print("VRAM GB:", round(torch.cuda.get_device_properties(0).total_memory/1024**3,2) if torch.cuda.is_available() else 0)' | & $Py - 2>&1
    $Report.Add(($Hardware | Out-String))
    if ($LASTEXITCODE -ne 0) { $Failed++ }
    foreach ($Name in @('gpu-preview-report.json','output-migration.json')) {
        $Path = Join-Path $Root ('Temp\QOL-Work\' + $Name)
        $Report.Add("Vorhandener Bericht: $Path | vorhanden: $(Test-Path -LiteralPath $Path)")
    }
} catch {
    $Failed++
    $Report.Add($_.Exception.Message)
} finally {
    Write-Host '############################################################'
    Write-Host 'KOPIERBLOCK FÜR CHATGPT - AB HIER KOPIEREN'
    Write-Host '=== VOCAL X QOL CHECK ==='
    Write-Host "Projekt: $Root"
    Write-Host "Python: $Py"
    Write-Host "Logs: $LogDir"
    Write-Host "Fehlgeschlagene Checks: $Failed"
    $Report | ForEach-Object { Write-Host $_ }
    Write-Host 'KOPIERBLOCK ENDE'
    Write-Host '############################################################'
}
exit ([int]($Failed -gt 0))
