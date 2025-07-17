#!/bin/bash

USER=$(whoami)

echo "🔪 Killing old processes..."
pkill -f "watch_input_and_run"
pkill -f "main.py"

echo "🔍 Checking leftover processes..."
ps aux | grep watch | grep -v grep

# === Path logic ===
if [ "$USER" == "admin" ]; then
  SHARED_DIR="/home/admin/shared_comfy_data"
  COMFYUI_PATH="/home/admin/ComfyUI/LinuxOS"
else
  SHARED_DIR="/home/shared_comfy_data"
  COMFYUI_PATH="/home/$USER/ComfyUI/LinuxOS"
fi

echo "🧭 Detected user: $USER — Running in $( [[ $USER == admin ]] && echo PROD || echo DEV ) mode"
echo "📂 Listing contents of shared input folder..."
ls -lah "$SHARED_DIR"

echo "🚀 Restarting ComfyUI watcher..."
cd "$COMFYUI_PATH" && ./watch_input_and_run.sh
