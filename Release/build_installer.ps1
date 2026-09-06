$ErrorActionPreference = "Stop"

$Release = $PSScriptRoot
$Root = Split-Path $Release -Parent
$LatestFile = Join-Path $Release "latest-app-candidate.json"
$InstallerDir = Join-Path $Release "Installer"
$OutputDir = Join-Path $InstallerDir "Output"
$IssFile = Join-Path $InstallerDir "Vocal-X-0.1.0-beta.1.iss"

$Latest = Get-Content -LiteralPath $LatestFile -Raw -Encoding UTF8 | ConvertFrom-Json
$Candidate = [IO.Path]::GetFullPath((Join-Path $Root $Latest.path))

if (-not (Test-Path -LiteralPath $Candidate)) {
    throw "Candidate fehlt: $Candidate"
}

$ModelFiles = @(Get-ChildItem -LiteralPath (Join-Path $Candidate "Models") -File -Recurse -ErrorAction SilentlyContinue).Count

if ($ModelFiles -ne 0) {
    throw "Installer darf keine Models enthalten."
}

$ISCCPaths = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 7\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 7\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 7\ISCC.exe"
)

$ISCC = ""

foreach ($Path in $ISCCPaths) {
    if ($Path -and (Test-Path -LiteralPath $Path)) {
        $ISCC = $Path
        break
    }
}

if (-not $ISCC) {
    throw "Inno Setup 7 ISCC.exe nicht gefunden."
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

Get-ChildItem -LiteralPath $OutputDir -Force -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force

$env:VOCAL_X_CANDIDATE = $Candidate

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Out = Join-Path $env:TEMP "VocalX-ISCC-$Stamp.out"
$Err = Join-Path $env:TEMP "VocalX-ISCC-$Stamp.err"

$Proc = Start-Process `
    -FilePath $ISCC `
    -ArgumentList @("`"$IssFile`"") `
    -WorkingDirectory $InstallerDir `
    -RedirectStandardOutput $Out `
    -RedirectStandardError $Err `
    -Wait `
    -PassThru

Write-Host "CANDIDATE=$Candidate"
Write-Host "ISCC=$ISCC"
Write-Host "ISCC_EXIT=$($Proc.ExitCode)"
Write-Host "OUTPUT=$OutputDir"

if ($Proc.ExitCode -ne 0) {
    if (Test-Path -LiteralPath $Out) { Get-Content -LiteralPath $Out -Tail 40 }
    if (Test-Path -LiteralPath $Err) { Get-Content -LiteralPath $Err -Tail 40 }
    exit $Proc.ExitCode
}

exit 0
