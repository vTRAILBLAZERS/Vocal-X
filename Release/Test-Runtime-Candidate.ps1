$ErrorActionPreference = 'Stop'
$TaskRoot = Split-Path $PSScriptRoot -Parent
$TaskFailed = $false
$TaskResults = [System.Collections.Generic.List[string]]::new()
$TaskSaved = @{}
foreach ($TaskName in @('PYTHONHOME','PYTHONPATH','PATH','QT_QPA_PLATFORM')) {
    $TaskSaved[$TaskName] = [Environment]::GetEnvironmentVariable($TaskName, 'Process')
}
try {
    $TaskCandidate = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'latest-runtime-candidate.json') -Raw | ConvertFrom-Json
    $TaskBuild = [IO.Path]::GetFullPath((Join-Path $TaskRoot $TaskCandidate.path))
    $TaskAllowed = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'Staging')) + [IO.Path]::DirectorySeparatorChar
    if (-not $TaskBuild.StartsWith($TaskAllowed, [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid candidate path' }
    $env:PYTHONHOME = 'Z:\VocalX-Nonexistent-Python'
    $env:PYTHONPATH = 'Z:\VocalX-Nonexistent-Packages'
    $env:PATH = Join-Path $env:WINDIR 'System32'
    $TaskLog = Join-Path $TaskBuild 'runtime-probe.log'
    & (Join-Path $TaskBuild 'Runtime\python.exe') -B -X utf8 (Join-Path $PSScriptRoot 'probe_runtime.py') *> $TaskLog
    $TaskCode = $LASTEXITCODE
    $TaskResults.Add((Get-Content -LiteralPath $TaskLog -Raw))
    $TaskResults.Add("Probe Exitcode: $TaskCode")
    $TaskResults.Add("Log: $TaskLog")
    if ($TaskCode -ne 0) { $TaskFailed = $true }
} catch { $TaskFailed = $true; $TaskResults.Add($_.Exception.Message) }
finally {
    foreach ($TaskName in $TaskSaved.Keys) { [Environment]::SetEnvironmentVariable($TaskName, $TaskSaved[$TaskName], 'Process') }
    Write-Host '############################################################'
    Write-Host '# KOPIERBLOCK FÜR CHATGPT - AB HIER KOPIEREN'
    $TaskResults | ForEach-Object { Write-Host $_ }
    Write-Host "Runtime-Test fehlgeschlagen: $TaskFailed"
    Write-Host 'Vollstaendiger Modell-Audiotest / frischer Windows-PC: NICHT DURCHGEFUEHRT'
    Write-Host '# KOPIERBLOCK ENDE'
    Write-Host '############################################################'
}
exit ([int]$TaskFailed)
