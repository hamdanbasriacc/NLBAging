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

# Launch ComfyUI server in background
echo "🚀 Starting ComfyUI server..."
cd "$COMFYUI_DIR"
"$PYTHON_BIN" main.py --disable-auto-launch > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
cd "$SCRIPT_DIR"

# Launch the Python watcher
echo "👁️ Launching watcher..."
"$PYTHON_BIN" watch_input_and_run_linux.py &

# Clean single-line status
echo -n "⏳ Waiting for ComfyUI server to be ready..."
until curl -s http://127.0.0.1:8188 >/dev/null; do
    sleep 1
    echo -n "."
done
echo -e "\r✅ ComfyUI server is ready!                         "
