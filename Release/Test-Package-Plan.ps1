$ErrorActionPreference = 'Stop'
$TaskResults = [System.Collections.Generic.List[string]]::new()
$TaskFailed = $false
try {
    $TaskPython = Join-Path (Split-Path $PSScriptRoot -Parent) '.venv\Scripts\python.exe'
    foreach ($TaskScript in @('test_package_plan.py', 'package_plan.py')) {
        $TaskOutput = & $TaskPython -X utf8 (Join-Path $PSScriptRoot $TaskScript) 2>&1
        $TaskCode = $LASTEXITCODE
        $TaskResults.Add(($TaskOutput | Out-String))
        $TaskResults.Add("${TaskScript}: Exitcode $TaskCode")
        if ($TaskCode -ne 0) { $TaskFailed = $true }
    }
} catch { $TaskFailed = $true; $TaskResults.Add($_.Exception.Message) }
finally {
    Write-Host '############################################################'
    Write-Host '# KOPIERBLOCK FÜR CHATGPT - AB HIER KOPIEREN'
    $TaskResults | ForEach-Object { Write-Host $_ }
    Write-Host "Pruefung fehlgeschlagen: $TaskFailed"
    Write-Host 'Installer erstellt: NEIN. Externe Freigabe: NEIN.'
    Write-Host '# KOPIERBLOCK ENDE'
    Write-Host '############################################################'
}
exit ([int]$TaskFailed)
