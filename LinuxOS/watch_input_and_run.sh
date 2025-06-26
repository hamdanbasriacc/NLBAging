#!/bin/bash

# Set working directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFYUI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INPUT_DIR="$SCRIPT_DIR/input"
OUTPUT_DIR="$SCRIPT_DIR/output"
PYTHON_BIN="$COMFYUI_DIR/venv/bin/python"
LOG_FILE="$SCRIPT_DIR/comfyui.log"

# Show which Python is used
echo "🐍 Using Python: $PYTHON_BIN"

# Check if requirements already installed
if [ ! -f "$COMFYUI_DIR/venv/.requirements_installed" ]; then
    echo "📦 Installing Python requirements..."
    "$PYTHON_BIN" -m pip install --upgrade pip
    "$PYTHON_BIN" -m pip install -r "$COMFYUI_DIR/requirements.txt"
    touch "$COMFYUI_DIR/venv/.requirements_installed"
else
    echo "✅ Python requirements already installed."
fi

# Launch ComfyUI server in the background and log output
echo "🚀 Starting ComfyUI server..."
cd "$COMFYUI_DIR"
"$PYTHON_BIN" main.py --disable-auto-launch > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
cd "$SCRIPT_DIR"

# Launch the Python watcher
echo "👁️ Launching watcher..."
"$PYTHON_BIN" watch_input_and_run_linux.py &

# Wait for ComfyUI server to be ready
RETRIES=60
for ((i=1; i<=RETRIES; i++)); do
    if curl -s http://127.0.0.1:8188 | grep -q "ComfyUI version"; then
        echo -e "\r✅ ComfyUI server is ready!                  "
        exit 0
    fi
    echo -ne "\r⏳ Waiting for ComfyUI server to be ready... ($i/$RETRIES)"
    sleep 1
done

# If it failed, print error
echo -e "\n❌ Timeout waiting for server. Check $LOG_FILE for details."
