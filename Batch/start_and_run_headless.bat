@echo off
echo 🤖 Batch started: %date% %time% >> C:\ComfyUI-CLI\watcher_log.txt
cd /d C:\ComfyUI-CLI

:: Set variables
set PYTHON=venv\Scripts\python.exe
set API_URL=http://127.0.0.1:8188/object_info

echo Launching ComfyUI server...
start "" /B %PYTHON% main.py

echo Waiting for ComfyUI server to be ready...
:wait_loop
curl --silent --head --fail %API_URL% >nul 2>&1
if errorlevel 1 (
    timeout /t 1 >nul
    goto wait_loop
)

echo ✅ ComfyUI is ready.
echo 🚀 Running headless automation...

:: Run headless script IN THE SAME TERMINAL (important!)
call Batch\run_comfyui_headless_aging.bat

echo ✅ All tasks completed.
exit
