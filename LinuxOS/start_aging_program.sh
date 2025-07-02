#!/bin/bash

echo "🌀 Aging Program is Starting..." >> /home/hamdan_basri/ComfyUI/LinuxOS/comfyui_log.txt
cd /home/hamdan_basri/ComfyUI/LinuxOS
exec ./watch_input_and_run.sh >> /home/hamdan_basri/ComfyUI/LinuxOS/comfyui_log.txt 2>&1
