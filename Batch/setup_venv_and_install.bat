@echo off
setlocal enabledelayedexpansion

:: ---- CONFIG ----
set VENV_DIR=venv
set PYTHON=python
set REQUIREMENTS=requirements.txt

:: ---- STEP 1: Create venv ----
echo 🔧 Creating virtual environment...
%PYTHON% -m venv %VENV_DIR%

if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ✅ Virtual environment created at %VENV_DIR%
) else (
    echo ❌ Failed to create virtual environment
    exit /b 1
)

:: ---- STEP 2: Activate venv ----
echo 🔁 Activating venv...
call %VENV_DIR%\Scripts\activate.bat

:: ---- STEP 3: Upgrade pip ----
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

:: ---- STEP 4: Install requirements ----
echo 📦 Installing Python dependencies...
if exist %REQUIREMENTS% (
    pip install -r %REQUIREMENTS%
) else (
    echo ❌ requirements.txt not found! Creating default list...

    :: Generate fallback requirements
    echo torch>> %REQUIREMENTS%
    echo torchvision>> %REQUIREMENTS%
    echo fastapi>> %REQUIREMENTS%
    echo uvicorn>> %REQUIREMENTS%
    echo requests>> %REQUIREMENTS%
    echo pillow>> %REQUIREMENTS%
    echo pyyaml>> %REQUIREMENTS%
    echo tqdm>> %REQUIREMENTS%
    echo numpy>> %REQUIREMENTS%
    pip install -r %REQUIREMENTS%
)

:: ---- STEP 5: Optional Test Launch ----
echo 🚀 Setup complete. You can now run:
echo    venv\Scripts\python.exe main.py

pause
