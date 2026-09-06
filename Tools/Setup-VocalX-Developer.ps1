param(
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================"
Write-Host " VOCAL X - DEVELOPER SETUP"
Write-Host "============================================================"
Write-Host ""

# ------------------------------------------------------------
# Git
# ------------------------------------------------------------

$GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
$GitAvailable = ($null -ne $GitCommand)
$GitRepository = Test-Path -LiteralPath (Join-Path $ProjectRoot ".git")
$GitBranch = "NOT AVAILABLE"

if ($GitAvailable -and $GitRepository) {
    $GitBranch = git branch --show-current
}

# ------------------------------------------------------------
# Windows
# ------------------------------------------------------------

$WindowsVersion = [System.Environment]::OSVersion.VersionString

# ------------------------------------------------------------
# NVIDIA
# ------------------------------------------------------------

$NvidiaCommand = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
$NvidiaAvailable = ($null -ne $NvidiaCommand)
$GpuName = "NOT DETECTED"

if ($NvidiaAvailable) {
    try {
        $GpuName = nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1
    }
    catch {
        $GpuName = "DETECTION FAILED"
    }
}

# ------------------------------------------------------------
# Python 3.12
# ------------------------------------------------------------

$Python312Available = $false
$Python312Version = "NOT FOUND"
$Python312Command = $null

$PyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue

if ($null -ne $PyLauncher) {
    try {
        $TestVersion = py -3.12 --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $Python312Available = $true
            $Python312Version = $TestVersion
            $Python312Command = "py -3.12"
        }
    }
    catch {}
}

if (-not $Python312Available) {
    $PythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -ne $PythonCommand) {
        try {
            $VersionText = python --version 2>&1
            if ($VersionText -match "Python 3\.12\.") {
                $Python312Available = $true
                $Python312Version = $VersionText
                $Python312Command = $PythonCommand.Source
            }
        }
        catch {}
    }
}

# ------------------------------------------------------------
# Existing Vocal X environments
# ------------------------------------------------------------

$MainVenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$AnyVenvPython = Join-Path $ProjectRoot ".venv-anyenhance\Scripts\python.exe"

$MainVenvExists = Test-Path -LiteralPath $MainVenvPython
$AnyVenvExists = Test-Path -LiteralPath $AnyVenvPython

# ------------------------------------------------------------
# Find OneDrive roots
# ------------------------------------------------------------

$OneDriveRoots = @()

foreach ($VariableName in @("OneDrive","OneDriveCommercial","OneDriveConsumer")) {
    $Value = [Environment]::GetEnvironmentVariable($VariableName)
    if ($Value -and (Test-Path -LiteralPath $Value)) {
        $OneDriveRoots += $Value
    }
}

if ($env:USERPROFILE -and (Test-Path -LiteralPath $env:USERPROFILE)) {
    $OneDriveFolders = @(
        Get-ChildItem -LiteralPath $env:USERPROFILE -Directory -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "OneDrive*" }
    )

    foreach ($Folder in $OneDriveFolders) {
        $OneDriveRoots += $Folder.FullName
    }
}

$OneDriveRoots = @($OneDriveRoots | Select-Object -Unique)

# ------------------------------------------------------------
# Find shared Vocal X asset root
# ------------------------------------------------------------

$VocalXAssetRoot = $null

foreach ($OneDriveRoot in $OneDriveRoots) {

    $Candidates = @(
        (Join-Path $OneDriveRoot "TRAILBLAZERS Sounds\Vocal X"),
        (Join-Path $OneDriveRoot "Vocal X")
    )

    foreach ($Candidate in $Candidates) {

        $CandidateModels = Join-Path $Candidate "Modelle"
        $CandidateRuntime = Join-Path $Candidate "Developer Assets\Runtime"

        if ((Test-Path -LiteralPath $CandidateModels) -and (Test-Path -LiteralPath $CandidateRuntime)) {
            $VocalXAssetRoot = $Candidate
            break
        }
    }

    if ($null -ne $VocalXAssetRoot) {
        break
    }
}

$OneDriveAssetsFound = ($null -ne $VocalXAssetRoot)

# ------------------------------------------------------------
# Asset checks
# ------------------------------------------------------------

$ModelSource = $null
$RuntimeSource = $null
$ModelFileCount = 0
$ModelSizeBytes = 0
$AnyV1RuntimeFound = $false
$Any360RuntimeFound = $false

if ($OneDriveAssetsFound) {

    $ModelSource = Join-Path $VocalXAssetRoot "Modelle"
    $RuntimeSource = Join-Path $VocalXAssetRoot "Developer Assets\Runtime"

    $ModelFiles = @(
        Get-ChildItem -LiteralPath $ModelSource -Recurse -File -Force -ErrorAction SilentlyContinue
    )

    $ModelFileCount = $ModelFiles.Count

    $ModelSizeBytes = ($ModelFiles | Measure-Object Length -Sum).Sum
    if ($null -eq $ModelSizeBytes) {
        $ModelSizeBytes = 0
    }

    $AnyV1RuntimeFound = Test-Path -LiteralPath (Join-Path $RuntimeSource "AnyEnhance-v1")
    $Any360RuntimeFound = Test-Path -LiteralPath (Join-Path $RuntimeSource "AnyEnhance-360M-Recovered")
}

$ModelSizeGB = [math]::Round($ModelSizeBytes / 1GB, 2)

# ------------------------------------------------------------
# Current local models
# ------------------------------------------------------------

$LocalModels = Join-Path $ProjectRoot "Models"
$LocalModelsExist = Test-Path -LiteralPath $LocalModels

# ------------------------------------------------------------
# Git hook
# ------------------------------------------------------------

$HookFile = Join-Path $ProjectRoot ".githooks\pre-push"
$HookExists = Test-Path -LiteralPath $HookFile
$HookConfigured = $false

if ($GitAvailable -and $GitRepository) {
    $CurrentHooksPath = git config --local core.hooksPath
    $HookConfigured = ($CurrentHooksPath -eq ".githooks")
}

# ------------------------------------------------------------
# Final preflight result
# ------------------------------------------------------------

$AssetsComplete = (
    $OneDriveAssetsFound -and
    $ModelFileCount -gt 0 -and
    $AnyV1RuntimeFound -and
    $Any360RuntimeFound
)

$PreflightPassed = (
    $GitAvailable -and
    $GitRepository -and
    $NvidiaAvailable -and
    $AssetsComplete
)

############################################################
# KOPIERBLOCK FUER CHATGPT - AB HIER KOPIEREN
############################################################

Write-Host ""
Write-Host "=== VOCAL X DEVELOPER SETUP PREFLIGHT ==="
Write-Host ""

Write-Host "PROJECT ROOT:"
Write-Host $ProjectRoot

Write-Host ""
Write-Host "GIT AVAILABLE:"
Write-Host $GitAvailable

Write-Host ""
Write-Host "GIT REPOSITORY:"
Write-Host $GitRepository

Write-Host ""
Write-Host "GIT BRANCH:"
Write-Host $GitBranch

Write-Host ""
Write-Host "WINDOWS:"
Write-Host $WindowsVersion

Write-Host ""
Write-Host "NVIDIA AVAILABLE:"
Write-Host $NvidiaAvailable

Write-Host ""
Write-Host "GPU:"
Write-Host $GpuName

Write-Host ""
Write-Host "PYTHON 3.12 AVAILABLE:"
Write-Host $Python312Available

Write-Host ""
Write-Host "PYTHON 3.12 VERSION:"
Write-Host $Python312Version

Write-Host ""
Write-Host "MAIN VENV EXISTS:"
Write-Host $MainVenvExists

Write-Host ""
Write-Host "ANYENHANCE VENV EXISTS:"
Write-Host $AnyVenvExists

Write-Host ""
Write-Host "ONEDRIVE ROOTS DETECTED:"
Write-Host $OneDriveRoots.Count

foreach ($RootPath in $OneDriveRoots) {
    Write-Host $RootPath
}

Write-Host ""
Write-Host "VOCAL X ONEDRIVE ASSETS FOUND:"
Write-Host $OneDriveAssetsFound

Write-Host ""
Write-Host "VOCAL X ASSET ROOT:"
if ($OneDriveAssetsFound) {
    Write-Host $VocalXAssetRoot
}
else {
    Write-Host "NOT FOUND"
}

Write-Host ""
Write-Host "MODEL SOURCE:"
if ($ModelSource) { Write-Host $ModelSource } else { Write-Host "NOT FOUND" }

Write-Host ""
Write-Host "MODEL FILE COUNT:"
Write-Host $ModelFileCount

Write-Host ""
Write-Host "MODEL SIZE GB:"
Write-Host $ModelSizeGB

Write-Host ""
Write-Host "ANYENHANCE V1 RUNTIME FOUND:"
Write-Host $AnyV1RuntimeFound

Write-Host ""
Write-Host "ANYENHANCE 360M RUNTIME FOUND:"
Write-Host $Any360RuntimeFound

Write-Host ""
Write-Host "LOCAL MODELS ALREADY EXIST:"
Write-Host $LocalModelsExist

Write-Host ""
Write-Host "GIT HOOK EXISTS:"
Write-Host $HookExists

Write-Host ""
Write-Host "GIT HOOK CONFIGURED:"
Write-Host $HookConfigured

Write-Host ""
Write-Host "ASSETS COMPLETE:"
Write-Host $AssetsComplete

Write-Host ""
Write-Host "PREFLIGHT PASSED:"
Write-Host $PreflightPassed

Write-Host ""
Write-Host "INSTALLATION PERFORMED:"
Write-Host "NO"

Write-Host ""
Write-Host "FILES MODIFIED BY PREFLIGHT:"
Write-Host "NO"

Write-Host ""
Write-Host "=== END VOCAL X DEVELOPER SETUP PREFLIGHT ==="

############################################################
# KOPIERBLOCK ENDE
############################################################

if ($PreflightOnly) {
    if ($PreflightPassed) { exit 0 } else { exit 10 }
}

# ------------------------------------------------------------
# Fallback: OneDrive folder selection
# ------------------------------------------------------------

if (-not $OneDriveAssetsFound) {

    Write-Host ""
    Write-Host "[INFO] Vocal X OneDrive assets were not detected automatically."
    Write-Host "[INFO] Please select the shared Vocal X folder."
    Write-Host ""

    try {
        Add-Type -AssemblyName System.Windows.Forms

        $Dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $Dialog.Description = "Select the shared Vocal X folder containing Modelle and Developer Assets"
        $Dialog.ShowNewFolderButton = $false

        $DialogResult = $Dialog.ShowDialog()

        if ($DialogResult -eq [System.Windows.Forms.DialogResult]::OK) {

            $Candidate = $Dialog.SelectedPath
            $CandidateModels = Join-Path $Candidate "Modelle"
            $CandidateRuntime = Join-Path $Candidate "Developer Assets\Runtime"

            if ((Test-Path -LiteralPath $CandidateModels) -and (Test-Path -LiteralPath $CandidateRuntime)) {

                $VocalXAssetRoot = $Candidate
                $ModelSource = $CandidateModels
                $RuntimeSource = $CandidateRuntime
                $OneDriveAssetsFound = $true

                $ModelFiles = @(
                    Get-ChildItem -LiteralPath $ModelSource -Recurse -File -Force -ErrorAction SilentlyContinue
                )

                $ModelFileCount = $ModelFiles.Count
                $ModelSizeBytes = ($ModelFiles | Measure-Object Length -Sum).Sum

                if ($null -eq $ModelSizeBytes) { $ModelSizeBytes = 0 }

                $ModelSizeGB = [math]::Round($ModelSizeBytes / 1GB, 2)

                $AnyV1RuntimeFound = Test-Path -LiteralPath (Join-Path $RuntimeSource "AnyEnhance-v1")
                $Any360RuntimeFound = Test-Path -LiteralPath (Join-Path $RuntimeSource "AnyEnhance-360M-Recovered")

                $AssetsComplete = (
                    $ModelFileCount -gt 0 -and
                    $AnyV1RuntimeFound -and
                    $Any360RuntimeFound
                )
            }
        }
    }
    catch {
        Write-Host "[WARNING] Folder selection failed."
    }
}

# ------------------------------------------------------------
# Final prerequisite decision
# ------------------------------------------------------------

$PreflightPassed = (
    $GitAvailable -and
    $GitRepository -and
    $NvidiaAvailable -and
    $AssetsComplete
)

if (-not $PreflightPassed) {

    Write-Host ""
    Write-Host "============================================================"
    Write-Host " VOCAL X SETUP CANNOT CONTINUE"
    Write-Host "============================================================"
    Write-Host ""

    if (-not $GitAvailable) {
        Write-Host "[FAIL] Git for Windows is missing."
    }

    if (-not $GitRepository) {
        Write-Host "[FAIL] This is not a cloned Vocal X Git repository."
    }

    if (-not $NvidiaAvailable) {
        Write-Host "[FAIL] Compatible NVIDIA environment was not detected."
    }

    if (-not $AssetsComplete) {
        Write-Host "[FAIL] Vocal X OneDrive developer assets are incomplete or unavailable."
    }

    exit 20
}

# ------------------------------------------------------------
# Installer files
# ------------------------------------------------------------

$AssetInstaller = Join-Path $ProjectRoot "Tools\Install-VocalX-Assets.ps1"
$PythonInstaller = Join-Path $ProjectRoot "Tools\Install-VocalX-Python.ps1"

if (-not (Test-Path -LiteralPath $AssetInstaller)) {
    Write-Host "[ERROR] Asset installer missing."
    exit 21
}

if (-not (Test-Path -LiteralPath $PythonInstaller)) {
    Write-Host "[ERROR] Python installer missing."
    exit 22
}

# ------------------------------------------------------------
# STEP 1 - Assets
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " STEP 1/4 - MODELS AND RUNTIME"
Write-Host "============================================================"
Write-Host ""

& powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File $AssetInstaller `
    -ProjectRoot $ProjectRoot `
    -AssetRoot $VocalXAssetRoot

$AssetExit = $LASTEXITCODE

if ($AssetExit -ne 0) {
    Write-Host "[ERROR] Vocal X asset installation failed."
    Write-Host "Exit code: $AssetExit"
    exit 23
}

# ------------------------------------------------------------
# STEP 2 - Check existing Python environment first
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " STEP 2/4 - PYTHON ENVIRONMENT"
Write-Host "============================================================"
Write-Host ""

Write-Host "[INFO] Checking whether the Vocal X Python environments are already valid..."
Write-Host ""

& powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File $PythonInstaller `
    -ProjectRoot $ProjectRoot `
    -VerifyOnly

$PythonVerifyBefore = $LASTEXITCODE
$PythonInstallPerformed = $false

if ($PythonVerifyBefore -ne 0) {

    Write-Host ""
    Write-Host "[INFO] Python environment is incomplete."
    Write-Host "[INFO] Starting automatic environment installation..."
    Write-Host ""

    & powershell.exe `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $PythonInstaller `
        -ProjectRoot $ProjectRoot

    $PythonInstallExit = $LASTEXITCODE
    $PythonInstallPerformed = $true

    if ($PythonInstallExit -ne 0) {
        Write-Host "[ERROR] Python environment installation failed."
        Write-Host "Exit code: $PythonInstallExit"
        exit 24
    }
}

# ------------------------------------------------------------
# STEP 3 - Mandatory post-install verification
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " STEP 3/4 - CUDA AND ENVIRONMENT VERIFICATION"
Write-Host "============================================================"
Write-Host ""

& powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File $PythonInstaller `
    -ProjectRoot $ProjectRoot `
    -VerifyOnly

$PythonVerifyAfter = $LASTEXITCODE

if ($PythonVerifyAfter -ne 0) {
    Write-Host "[ERROR] Final Python/CUDA verification failed."
    exit 25
}

# ------------------------------------------------------------
# STEP 4 - Source smoke test
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " STEP 4/4 - VOCAL X SMOKE TEST"
Write-Host "============================================================"
Write-Host ""

$MainPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$GuiFile = Join-Path $ProjectRoot "App\vocal_gui.py"
$PipelineFile = Join-Path $ProjectRoot "App\pipeline.py"

$SmokeImportOK = $false
$SourceCompileOK = $false

try {

    & $MainPython -c "import torch, numpy, soundfile, PySide6; print('VOCAL_X_IMPORT_SMOKE_OK')"

    $SmokeImportOK = ($LASTEXITCODE -eq 0)
}
catch {
    $SmokeImportOK = $false
}

if ((Test-Path -LiteralPath $GuiFile) -and (Test-Path -LiteralPath $PipelineFile)) {

    try {

        & $MainPython -m py_compile $GuiFile $PipelineFile

        $SourceCompileOK = ($LASTEXITCODE -eq 0)
    }
    catch {
        $SourceCompileOK = $false
    }
}

$ModelsInstalled = Test-Path -LiteralPath (Join-Path $ProjectRoot "Models")
$AnyV1Installed = Test-Path -LiteralPath (Join-Path $ProjectRoot "Tools\AnyEnhance-v1")
$Any360Installed = Test-Path -LiteralPath (Join-Path $ProjectRoot "Tools\AnyEnhance-360M-Recovered")

$FinalReady = (
    $AssetExit -eq 0 -and
    $PythonVerifyAfter -eq 0 -and
    $SmokeImportOK -and
    $SourceCompileOK -and
    $ModelsInstalled -and
    $AnyV1Installed -and
    $Any360Installed
)

############################################################
# KOPIERBLOCK FUER CHATGPT - AB HIER KOPIEREN
############################################################

Write-Host ""
Write-Host "=== VOCAL X ONE CLICK SETUP STATUS ==="
Write-Host ""

Write-Host "ASSET ROOT:"
Write-Host $VocalXAssetRoot

Write-Host ""
Write-Host "ASSET INSTALL EXIT CODE:"
Write-Host $AssetExit

Write-Host ""
Write-Host "PYTHON VERIFIED BEFORE INSTALL:"
Write-Host ($PythonVerifyBefore -eq 0)

Write-Host ""
Write-Host "PYTHON INSTALL PERFORMED:"
Write-Host $PythonInstallPerformed

Write-Host ""
Write-Host "PYTHON VERIFIED AFTER SETUP:"
Write-Host ($PythonVerifyAfter -eq 0)

Write-Host ""
Write-Host "IMPORT SMOKE TEST:"
Write-Host $SmokeImportOK

Write-Host ""
Write-Host "SOURCE COMPILE TEST:"
Write-Host $SourceCompileOK

Write-Host ""
Write-Host "MODELS INSTALLED:"
Write-Host $ModelsInstalled

Write-Host ""
Write-Host "ANYENHANCE V1 INSTALLED:"
Write-Host $AnyV1Installed

Write-Host ""
Write-Host "ANYENHANCE 360M INSTALLED:"
Write-Host $Any360Installed

Write-Host ""
Write-Host "VOCAL X DEVELOPER ENVIRONMENT READY:"
Write-Host $FinalReady

Write-Host ""
Write-Host "ACTIVATION:"
Write-Host "Developer activation is handled separately."

Write-Host ""
Write-Host "=== END VOCAL X ONE CLICK SETUP STATUS ==="

############################################################
# KOPIERBLOCK ENDE
############################################################

if ($FinalReady) {
    exit 0
}

exit 26
