$ErrorActionPreference = 'Stop'
$Results = [System.Collections.Generic.List[string]]::new()
try {
    $Root = Split-Path $PSScriptRoot -Parent
    $Py = Join-Path $Root '.venv\Scripts\python.exe'
    $Work = Join-Path $Root ('Temp\RestorationCheck-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $Work -Force | Out-Null
    foreach ($Script in @('test_pipeline.py','test_restoration.py')) {
        $Stdout = Join-Path $Work ($Script + '.stdout.txt')
        $Stderr = Join-Path $Work ($Script + '.stderr.txt')
        $Process = Start-Process -FilePath $Py -ArgumentList @('-X','utf8',('"' + (Join-Path $PSScriptRoot $Script) + '"')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr
        $Results.Add("$Script Exitcode: $($Process.ExitCode)")
        $Results.Add((Get-Content -LiteralPath $Stdout -Raw -Encoding UTF8))
        $Results.Add((Get-Content -LiteralPath $Stderr -Raw -Encoding UTF8))
        if ($Process.ExitCode -ne 0) { throw "$Script fehlgeschlagen" }
    }
    $Results.Add('Variante: AnyEnhance-v1 Baseline; Gesang experimentell.')
    $Results.Add('Diese Pruefung startet keine neue GPU-Inferenz.')
} catch { $Results.Add("FEHLER: $($_.Exception.Message)") }
finally {
    Write-Host "`n############################################################"
    Write-Host 'KOPIERBLOCK FÜR CHATGPT - AB HIER KOPIEREN'
    Write-Host '=== KI-RESTAURIERUNG ==='
    $Results | ForEach-Object { Write-Host $_ }
    Write-Host 'KOPIERBLOCK ENDE'
    Write-Host '############################################################'
}
