#!/bin/bash

LOG_FILE="/home/hamdan_basri/ComfyUI/LinuxOS/comfyui_log.txt"

echo "🌀 Aging Program is Starting..." | tee -a "$LOG_FILE"
cd /home/hamdan_basri/ComfyUI/LinuxOS
./watch_input_and_run.sh >> "$LOG_FILE" 2>&1 &
