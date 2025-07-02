#!/bin/bash

LOG_FILE="/home/hamdan_basri/ComfyUI/LinuxOS/comfyui_log.txt"
SCRIPT_DIR="/home/hamdan_basri/ComfyUI/LinuxOS"
COMFYUI_DIR="/home/hamdan_basri/ComfyUI"
PYTHON_BIN="$COMFYUI_DIR/venv/bin/python"

echo "🌀 Aging Program is Starting..." | tee -a "$LOG_FILE"

# Check and kill existing server on port 8188
if ss -ltn | grep -q ':8188'; then
    echo "🛑 Port 8188 in use, killing existing server..." | tee -a "$LOG_FILE"
    pkill -f "main.py"
    sleep 2
fi

# Start ComfyUI server in background
cd "$COMFYUI_DIR"
"$PYTHON_BIN" main.py --disable-auto-launch >> "$LOG_FILE" 2>&1 &

# Wait for server
echo "⏳ Waiting for ComfyUI server..." | tee -a "$LOG_FILE"
until curl -s http://127.0.0.1:8188 > /dev/null; do
    sleep 1
done
echo "✅ ComfyUI server is ready." | tee -a "$LOG_FILE"

# Launch watcher
cd "$SCRIPT_DIR"
echo "👁️ Starting watcher..." | tee -a "$LOG_FILE"
"$PYTHON_BIN" watch_input_and_run_linux.py >> "$LOG_FILE" 2>&1
