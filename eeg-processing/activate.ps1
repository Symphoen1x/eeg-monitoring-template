# Quick activation script for EEG Processing venv
Write-Host "Activating Python 3.10 virtual environment for EEG Processing..." -ForegroundColor Cyan
.\venv310\Scripts\Activate.ps1
Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
Write-Host "Python version: " -NoNewline
python --version
