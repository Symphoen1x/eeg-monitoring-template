# EEG Processing - Python 3.10 Virtual Environment Setup Script
# Run this script ONCE after installing Python 3.10

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  EEG Processing - VEnv Setup (Python 3.10)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Define Python 3.10 paths (common installation locations)
$python310Paths = @(
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "C:\Python310\python.exe",
    "$env:USERPROFILE\AppData\Local\Programs\Python\Python310\python.exe"
)

# Find Python 3.10
$python310 = $null
foreach ($path in $python310Paths) {
    if (Test-Path $path) {
        $python310 = $path
        Write-Host "[OK] Found Python 3.10 at: $path" -ForegroundColor Green
        break
    }
}

if (-not $python310) {
    Write-Host "[ERROR] Python 3.10 not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.10 from: https://www.python.org/downloads/release/python-31011/" -ForegroundColor Yellow
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Verify Python version
Write-Host ""
Write-Host "Verifying Python version..." -ForegroundColor Cyan
$version = & $python310 --version
Write-Host "  $version" -ForegroundColor Green

if ($version -notmatch "Python 3\.10") {
    Write-Host "[WARNING] Expected Python 3.10, but found: $version" -ForegroundColor Yellow
    Write-Host "Continue anyway? (Y/N): " -NoNewline
    $response = Read-Host
    if ($response -ne "Y" -and $response -ne "y") {
        exit 1
    }
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment 'venv310'..." -ForegroundColor Cyan
& $python310 -m venv venv310

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Virtual environment created" -ForegroundColor Green

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
$venvActivate = ".\venv310\Scripts\Activate.ps1"

# Check execution policy
$currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
if ($currentPolicy -eq "Restricted" -or $currentPolicy -eq "AllSigned") {
    Write-Host "[INFO] Adjusting PowerShell execution policy..." -ForegroundColor Yellow
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    Write-Host "[OK] Execution policy set to RemoteSigned" -ForegroundColor Green
}

& $venvActivate

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet
Write-Host "[OK] pip upgraded" -ForegroundColor Green

# Install requirements
Write-Host ""
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Cyan
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] All dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Some dependencies failed to install" -ForegroundColor Red
        Write-Host "Check the output above for details" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARNING] requirements.txt not found" -ForegroundColor Yellow
}

# Verify muselsl installation
Write-Host ""
Write-Host "Verifying muselsl installation..." -ForegroundColor Cyan
$muselslCheck = python -c "import muselsl; print('muselsl version:', muselsl.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] $muselslCheck" -ForegroundColor Green
} else {
    Write-Host "[WARNING] muselsl not properly installed" -ForegroundColor Yellow
}

# Create activation shortcut script
Write-Host ""
Write-Host "Creating activation shortcut 'activate.ps1'..." -ForegroundColor Cyan
$activateScript = @"
# Quick activation script for EEG Processing venv
Write-Host "Activating Python 3.10 virtual environment for EEG Processing..." -ForegroundColor Cyan
.\venv310\Scripts\Activate.ps1
Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
Write-Host "Python version: " -NoNewline
python --version
"@

Set-Content -Path "activate.ps1" -Value $activateScript
Write-Host "[OK] Created 'activate.ps1' shortcut" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Virtual environment is activated in this terminal" -ForegroundColor White
Write-Host "  2. To activate in the future, run: .\activate.ps1" -ForegroundColor White
Write-Host "  3. Pair your Muse 2 device via Bluetooth" -ForegroundColor White
Write-Host "  4. Run: python -m muselsl stream" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
