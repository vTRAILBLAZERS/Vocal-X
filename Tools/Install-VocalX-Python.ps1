param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectRoot,
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"

$MainLock = Join-Path $ProjectRoot "Config\requirements-main.lock.txt"
$AnyLock = Join-Path $ProjectRoot "Config\requirements-anyenhance.lock.txt"
$MainPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$AnyPython = Join-Path $ProjectRoot ".venv-anyenhance\Scripts\python.exe"

function Find-Python312 {
    $PyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        try {
            $Path = & $PyLauncher.Source -3.12 -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $Path -and (Test-Path -LiteralPath $Path)) { return $Path.Trim() }
        }
        catch {}
    }

    $LocalPython = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
    if (Test-Path -LiteralPath $LocalPython) { return $LocalPython }

    $PythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        try {
            $Version = & $PythonCommand.Source -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))"
            if ($Version.Trim() -eq "3.12") { return $PythonCommand.Source }
        }
        catch {}
    }

    return $null
}

function Get-TorchStatus {
    param([string]$Python)

    $Result = [ordered]@{
        Exists = $false
        Python = "NOT FOUND"
        Torch = "NOT FOUND"
        TorchCuda = "NOT FOUND"
        CudaAvailable = $false
        GPU = "NOT AVAILABLE"
    }

    if (-not (Test-Path -LiteralPath $Python)) {
        return [PSCustomObject]$Result
    }

    $Result.Exists = $true

    try { $Result.Python = (& $Python --version 2>&1).ToString().Trim() } catch {}

    try {
        $Values = @(& $Python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NOT AVAILABLE')" 2>&1)

        if ($LASTEXITCODE -eq 0 -and $Values.Count -ge 4) {
            $Result.Torch = $Values[0].ToString().Trim()
            $Result.TorchCuda = $Values[1].ToString().Trim()
            $Result.CudaAvailable = ($Values[2].ToString().Trim() -eq "True")
            $Result.GPU = $Values[3].ToString().Trim()
        }
    }
    catch {}

    return [PSCustomObject]$Result
}

if (-not (Test-Path -LiteralPath $MainLock)) {
    Write-Host "[ERROR] Main dependency lock missing:"
    Write-Host $MainLock
    exit 41
}

if (-not (Test-Path -LiteralPath $AnyLock)) {
    Write-Host "[ERROR] AnyEnhance dependency lock missing:"
    Write-Host $AnyLock
    exit 42
}

$SystemPython = Find-Python312

if (-not $SystemPython -and -not $VerifyOnly) {
    Write-Host ""
    Write-Host "[INFO] Python 3.12 not found."
    Write-Host "[INFO] Attempting automatic installation with winget..."
    Write-Host ""

    $Winget = Get-Command winget.exe -ErrorAction SilentlyContinue

    if (-not $Winget) {
        Write-Host "[ERROR] winget is not available."
        exit 43
    }

    & $Winget.Source install --id Python.Python.3.12 -e --source winget --scope user --silent --accept-package-agreements --accept-source-agreements

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Automatic Python installation failed."
        exit 44
    }

    Start-Sleep -Seconds 2
    $SystemPython = Find-Python312
}

$Python312Found = ($null -ne $SystemPython)

if (-not $VerifyOnly) {

    if (-not $Python312Found) {
        Write-Host "[ERROR] Python 3.12 could not be located."
        exit 45
    }

    if (-not (Test-Path -LiteralPath $MainPython)) {
        Write-Host ""
        Write-Host "[INFO] Creating main Vocal X environment..."
        & $SystemPython -m venv (Join-Path $ProjectRoot ".venv")
        if ($LASTEXITCODE -ne 0) { exit 46 }
    }

    if (-not (Test-Path -LiteralPath $AnyPython)) {
        Write-Host ""
        Write-Host "[INFO] Creating AnyEnhance environment..."
        & $SystemPython -m venv (Join-Path $ProjectRoot ".venv-anyenhance")
        if ($LASTEXITCODE -ne 0) { exit 47 }
    }

    Write-Host ""
    Write-Host "[INFO] Updating main environment package tools..."
    & $MainPython -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) { exit 48 }

    Write-Host ""
    Write-Host "[INFO] Installing main Vocal X dependencies..."
    & $MainPython -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -r $MainLock
    if ($LASTEXITCODE -ne 0) { exit 49 }

    Write-Host ""
    Write-Host "[INFO] Updating AnyEnhance environment package tools..."
    & $AnyPython -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) { exit 50 }

    Write-Host ""
    Write-Host "[INFO] Installing AnyEnhance dependencies..."
    & $AnyPython -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -r $AnyLock
    if ($LASTEXITCODE -ne 0) { exit 51 }
}

$MainStatus = Get-TorchStatus -Python $MainPython
$AnyStatus = Get-TorchStatus -Python $AnyPython

$NvidiaCommand = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
$NvidiaAvailable = ($null -ne $NvidiaCommand)
$NvidiaGPU = "NOT DETECTED"

if ($NvidiaAvailable) {
    try {
        $NvidiaGPU = (nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1).Trim()
    }
    catch {}
}

$MainCorrect = (
    $MainStatus.Exists -and
    $MainStatus.Python -match "Python 3\.12\." -and
    $MainStatus.Torch -eq "2.11.0+cu128" -and
    $MainStatus.TorchCuda -eq "12.8" -and
    $MainStatus.CudaAvailable
)

$AnyCorrect = (
    $AnyStatus.Exists -and
    $AnyStatus.Python -match "Python 3\.12\." -and
    $AnyStatus.Torch -eq "2.11.0+cu128" -and
    $AnyStatus.TorchCuda -eq "12.8" -and
    $AnyStatus.CudaAvailable
)

$EnvironmentVerified = (
    $NvidiaAvailable -and
    $MainCorrect -and
    $AnyCorrect
)

Write-Host ""
Write-Host "=== VOCAL X PYTHON ENVIRONMENT STATUS ==="
Write-Host ""

Write-Host "SYSTEM PYTHON 3.12 FOUND:"
Write-Host $Python312Found

Write-Host ""
Write-Host "SYSTEM PYTHON:"
if ($SystemPython) { Write-Host $SystemPython } else { Write-Host "NOT FOUND" }

Write-Host ""
Write-Host "NVIDIA AVAILABLE:"
Write-Host $NvidiaAvailable

Write-Host ""
Write-Host "NVIDIA GPU:"
Write-Host $NvidiaGPU

Write-Host ""
Write-Host "MAIN VENV EXISTS:"
Write-Host $MainStatus.Exists

Write-Host ""
Write-Host "MAIN PYTHON:"
Write-Host $MainStatus.Python

Write-Host ""
Write-Host "MAIN TORCH:"
Write-Host $MainStatus.Torch

Write-Host ""
Write-Host "MAIN TORCH CUDA:"
Write-Host $MainStatus.TorchCuda

Write-Host ""
Write-Host "MAIN CUDA AVAILABLE:"
Write-Host $MainStatus.CudaAvailable

Write-Host ""
Write-Host "MAIN GPU:"
Write-Host $MainStatus.GPU

Write-Host ""
Write-Host "MAIN ENVIRONMENT VERIFIED:"
Write-Host $MainCorrect

Write-Host ""
Write-Host "ANYENHANCE VENV EXISTS:"
Write-Host $AnyStatus.Exists

Write-Host ""
Write-Host "ANYENHANCE PYTHON:"
Write-Host $AnyStatus.Python

Write-Host ""
Write-Host "ANYENHANCE TORCH:"
Write-Host $AnyStatus.Torch

Write-Host ""
Write-Host "ANYENHANCE TORCH CUDA:"
Write-Host $AnyStatus.TorchCuda

Write-Host ""
Write-Host "ANYENHANCE CUDA AVAILABLE:"
Write-Host $AnyStatus.CudaAvailable

Write-Host ""
Write-Host "ANYENHANCE GPU:"
Write-Host $AnyStatus.GPU

Write-Host ""
Write-Host "ANYENHANCE ENVIRONMENT VERIFIED:"
Write-Host $AnyCorrect

Write-Host ""
Write-Host "FULL PYTHON ENVIRONMENT VERIFIED:"
Write-Host $EnvironmentVerified

Write-Host ""
Write-Host "VERIFY ONLY:"
Write-Host $VerifyOnly

Write-Host ""
Write-Host "=== END VOCAL X PYTHON ENVIRONMENT STATUS ==="

if ($EnvironmentVerified) { exit 0 }
exit 52
