@echo off
:: %1 is the image filename passed in
set IMAGE=%1

:: Run the headless script with image param
C:\ComfyUI-CLI\venv\Scripts\python.exe C:\ComfyUI-CLI\Batch\headless_api_runner.py "%IMAGE%"
