# ==============================================================================
# 🛠️ TRUST APP: TOTAL RESET & LAUNCH SCRIPT (FORCE PYTHON 3.9)
# ==============================================================================
$ErrorActionPreference = "Stop"
Write-Host "--- 1. SCORCHED EARTH CLEANUP ---" -ForegroundColor Cyan

# Kill any existing uvicorn processes to free up the port
Stop-Process -Name "uvicorn" -ErrorAction SilentlyContinue

# Delete the broken virtual environment
if (Test-Path "venv") { 
    Write-Host "Removing broken venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv 
}

# --- 2. IDENTIFY PYTHON 3.9 PATH ---
$P39 = "$env:USERPROFILE\AppData\Local\Programs\Python\Python39\python.exe"

if (!(Test-Path $P39)) {
    Write-Host "❌ ERROR: Python 3.9 was not found at $P39" -ForegroundColor Red
    Write-Host "Please install Python 3.9 or update the path in this script."
    exit
}

# --- 3. CREATE ISOLATED ENVIRONMENT ---
Write-Host "--- 2. CREATING ISOLATED PYTHON 3.9 ENV ---" -ForegroundColor Green
& $P39 -m venv venv

# Define paths to the isolated tools inside the new venv
$isolated_python = "$(Get-Location)\venv\Scripts\python.exe"
$isolated_pip    = "$(Get-Location)\venv\Scripts\pip.exe"
$isolated_uvicorn = "$(Get-Location)\venv\Scripts\uvicorn.exe"

# Force the Environment Path to prioritize the venv
$env:PATH = "$(Get-Location)\venv\Scripts;" + $env:PATH

# --- 4. INSTALL THE 'GOLDEN STACK' (Version Locked) ---
Write-Host "--- 3. INSTALLING COMPATIBLE LIBRARIES ---" -ForegroundColor Cyan

# Upgrade pip inside the venv first
& $isolated_python -m pip install --upgrade pip

# Install Protobuf 3.20.3 FIRST (Crucial for the 'Descriptors' fix)
Write-Host "Installing Protobuf 3.20.3..."
& $isolated_pip install "protobuf==3.20.3"

# Install NumPy 1.24.3 (Crucial for Python 3.9 + TF 2.11)
Write-Host "Installing NumPy 1.24.3..."
& $isolated_pip install "numpy==1.24.3"

Write-Host "Installing pandas"
& $isolated_pip install "pandas"

# Install the rest of the AI and Web stack
Write-Host "Installing TensorFlow, Gemini SDK, and FastAPI..."
& $isolated_pip install tensorflow==2.11.0 google-genai==0.3.0 fastapi uvicorn joblib h5py scikit-learn python-multipart

# --- 5. CONFIGURATION ---
$env:GEMINI_API_KEY = "xxx"

# --- 6. FINAL VERIFICATION ---
Write-Host "`n--- 4. FINAL SYSTEM CHECK ---" -ForegroundColor Magenta
$check_ver = & $isolated_python --version
Write-Host "Running on: $check_ver"

& $isolated_python -c "import tensorflow as tf; import google.genai; print('✅ SUCCESS: TensorFlow ' + tf.__version__ + ' and GenAI are synced.')"

# --- 7. START SERVER ---
Write-Host "`n--- 5. LAUNCHING BACKEND ---" -ForegroundColor Green
Write-Host "Server starting at http://127.0.0.1:8000"
& $isolated_uvicorn main:app --reload