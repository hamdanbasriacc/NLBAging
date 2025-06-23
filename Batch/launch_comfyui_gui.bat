@echo off
cd /d C:\ComfyUI-CLI

:: Use system Python or your venv — update this if needed
set PYTHON=venv\Scripts\python.exe

echo Launching ComfyUI GUI...
%PYTHON% main.py

echo.
echo Press any key to close this window (server is running in browser)...
pause >nul
