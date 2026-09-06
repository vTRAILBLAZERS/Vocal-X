param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectRoot,

    [Parameter(Mandatory=$true)]
    [string]$AssetRoot
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================"
Write-Host " VOCAL X - INSTALL DEVELOPER ASSETS"
Write-Host "============================================================"
Write-Host ""

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    Write-Host "[ERROR] Project root not found:"
    Write-Host $ProjectRoot
    exit 31
}

if (-not (Test-Path -LiteralPath $AssetRoot)) {
    Write-Host "[ERROR] OneDrive asset root not found:"
    Write-Host $AssetRoot
    exit 32
}

$ModelSource = Join-Path $AssetRoot "Modelle"
$RuntimeSource = Join-Path $AssetRoot "Developer Assets\Runtime"

$ModelTarget = Join-Path $ProjectRoot "Models"
$AnyV1Source = Join-Path $RuntimeSource "AnyEnhance-v1"
$AnyV1Target = Join-Path $ProjectRoot "Tools\AnyEnhance-v1"
$Any360Source = Join-Path $RuntimeSource "AnyEnhance-360M-Recovered"
$Any360Target = Join-Path $ProjectRoot "Tools\AnyEnhance-360M-Recovered"

$RequiredSources = @(
    $ModelSource,
    $AnyV1Source,
    $Any360Source
)

foreach ($Source in $RequiredSources) {
    if (-not (Test-Path -LiteralPath $Source)) {
        Write-Host "[ERROR] Required asset source missing:"
        Write-Host $Source
        exit 33
    }
}

function Copy-VocalXAssetTree {
    param(
        [string]$Name,
        [string]$Source,
        [string]$Target
    )

    Write-Host ""
    Write-Host "------------------------------------------------------------"
    Write-Host $Name
    Write-Host "------------------------------------------------------------"
    Write-Host "Source:"
    Write-Host $Source
    Write-Host "Target:"
    Write-Host $Target
    Write-Host ""

    New-Item -ItemType Directory -Path $Target -Force | Out-Null

    $RoboOutput = robocopy `
        $Source `
        $Target `
        /E `
        /Z `
        /R:2 `
        /W:2 `
        /COPY:DAT `
        /DCOPY:DAT `
        /FFT `
        /NP

    $RoboCode = $LASTEXITCODE

    if ($RoboCode -gt 7) {
        Write-Host "[ERROR] Robocopy failed."
        Write-Host "Exit code: $RoboCode"
        return [PSCustomObject]@{
            Name = $Name
            Success = $false
            RoboCode = $RoboCode
            SourceFiles = 0
            VerifiedFiles = 0
            MissingFiles = 0
            SizeMismatch = 0
        }
    }

    $SourceFiles = @(
        Get-ChildItem `
            -LiteralPath $Source `
            -Recurse `
            -File `
            -Force `
            -ErrorAction SilentlyContinue
    )

    $Verified = 0
    $Missing = 0
    $Mismatch = 0

    foreach ($SourceFile in $SourceFiles) {

        $Relative = $SourceFile.FullName.Substring($Source.Length).TrimStart("\")
        $TargetFile = Join-Path $Target $Relative

        if (-not (Test-Path -LiteralPath $TargetFile)) {
            $Missing++
            continue
        }

        $TargetInfo = Get-Item -LiteralPath $TargetFile

        if ($TargetInfo.Length -ne $SourceFile.Length) {
            $Mismatch++
            continue
        }

        $Verified++
    }

    $Success = (
        $Missing -eq 0 -and
        $Mismatch -eq 0 -and
        $Verified -eq $SourceFiles.Count
    )

    return [PSCustomObject]@{
        Name = $Name
        Success = $Success
        RoboCode = $RoboCode
        SourceFiles = $SourceFiles.Count
        VerifiedFiles = $Verified
        MissingFiles = $Missing
        SizeMismatch = $Mismatch
    }
}

$Results = @()

$Results += Copy-VocalXAssetTree `
    -Name "Models" `
    -Source $ModelSource `
    -Target $ModelTarget

$Results += Copy-VocalXAssetTree `
    -Name "AnyEnhance-v1 Runtime" `
    -Source $AnyV1Source `
    -Target $AnyV1Target

$Results += Copy-VocalXAssetTree `
    -Name "AnyEnhance-360M Runtime" `
    -Source $Any360Source `
    -Target $Any360Target

$AllVerified = (
    @(
        $Results |
        Where-Object { -not $_.Success }
    ).Count -eq 0
)

$GitAvailable = ($null -ne (Get-Command git.exe -ErrorAction SilentlyContinue))
$GitRepo = Test-Path -LiteralPath (Join-Path $ProjectRoot ".git")
$HookExists = Test-Path -LiteralPath (Join-Path $ProjectRoot ".githooks\pre-push")
$HookConfigured = $false

if ($GitAvailable -and $GitRepo -and $HookExists) {
    Set-Location $ProjectRoot
    git config --local core.hooksPath .githooks
    $HookConfigured = ((git config --local core.hooksPath) -eq ".githooks")
}

############################################################
# KOPIERBLOCK FUER CHATGPT - AB HIER KOPIEREN
############################################################

Write-Host ""
Write-Host "=== VOCAL X ASSET INSTALLATION STATUS ==="

Write-Host ""
Write-Host "PROJECT ROOT:"
Write-Host $ProjectRoot

Write-Host ""
Write-Host "ASSET ROOT:"
Write-Host $AssetRoot

foreach ($Result in $Results) {

    Write-Host ""
    Write-Host "ASSET:"
    Write-Host $Result.Name

    Write-Host "ROBOCOPY EXIT CODE:"
    Write-Host $Result.RoboCode

    Write-Host "SOURCE FILES:"
    Write-Host $Result.SourceFiles

    Write-Host "VERIFIED FILES:"
    Write-Host $Result.VerifiedFiles

    Write-Host "MISSING FILES:"
    Write-Host $Result.MissingFiles

    Write-Host "SIZE MISMATCHES:"
    Write-Host $Result.SizeMismatch

    Write-Host "VERIFIED:"
    Write-Host $Result.Success
}

Write-Host ""
Write-Host "GIT HOOK CONFIGURED:"
Write-Host $HookConfigured

Write-Host ""
Write-Host "ALL ASSETS VERIFIED:"
Write-Host $AllVerified

Write-Host ""
Write-Host "FILES DELETED:"
Write-Host "NO"

Write-Host ""
Write-Host "VIRTUAL ENVIRONMENTS MODIFIED:"
Write-Host "NO"

Write-Host ""
Write-Host "=== END VOCAL X ASSET INSTALLATION STATUS ==="

############################################################
# KOPIERBLOCK ENDE
############################################################

if ($AllVerified -and $HookConfigured) {
    exit 0
}

exit 34
