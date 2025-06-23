@echo off
echo Starting watcher and ComfyUI server...

:: Define paths
set PYTHON=C:\ComfyUI-CLI\venv\Scripts\python.exe
set BATCH_DIR=C:\ComfyUI-CLI\Batch
set COMFY_DIR=C:\ComfyUI-CLI

:: Start ComfyUI server (once only!)
start "ComfyUI Server" /B %PYTHON% %COMFY_DIR%\main.py
echo ComfyUI server started...

:: Now run the watcher script (don't start ComfyUI again in there)
%PYTHON% %BATCH_DIR%\watch_input_and_run.py
