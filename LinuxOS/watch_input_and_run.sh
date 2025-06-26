#!/bin/bash

# Set working directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFYUI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INPUT_DIR="$SCRIPT_DIR/input"
OUTPUT_DIR="$SCRIPT_DIR/output"
PYTHON_BIN="$COMFYUI_DIR/venv/bin/python"
LOG_FILE="$SCRIPT_DIR/comfyui.log"

echo "🐍 Using Python: $PYTHON_BIN"

# Ensure requirements are installed once
if [ ! -f "$COMFYUI_DIR/venv/.requirements_installed" ]; then
    echo "📦 Installing Python requirements..."
    "$PYTHON_BIN" -m pip install --upgrade pip
    "$PYTHON_BIN" -m pip install -r "$COMFYUI_DIR/requirements.txt"
    touch "$COMFYUI_DIR/venv/.requirements_installed"
else
    echo "✅ Python requirements already installed."
fi

# Start ComfyUI server
echo "🚀 Starting ComfyUI server..."
cd "$COMFYUI_DIR"
"$PYTHON_BIN" main.py --disable-auto-launch > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
cd "$SCRIPT_DIR"

# Start watcher in background
echo "👁️ Launching watcher..."
"$PYTHON_BIN" watch_input_and_run_linux.py &
WATCHER_PID=$!

# Wait for ComfyUI server to be ready
echo -n "⏳ Waiting for ComfyUI server to be ready... "
RETRIES=60
for ((i=1; i<=RETRIES; i++)); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8188)
    if [[ "$STATUS" == "200" ]]; then
        echo -e "\r✅ ComfyUI server is ready!                  "
        break
    fi
    echo -ne "\r⏳ Waiting for ComfyUI server to be ready... ($i/$RETRIES)"
    sleep 1
done

if [[ "$i" -gt "$RETRIES" ]]; then
    echo -e "\n❌ Timeout waiting for server. Check $LOG_FILE for details."
    kill $SERVER_PID $WATCHER_PID 2>/dev/null
    exit 1
fi

# Wait forever (or Ctrl+C)
wait
