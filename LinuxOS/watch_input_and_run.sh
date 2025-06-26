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

# Check if requirements are installed
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
cd "$SCRIPT_DIR"

# Wait for the server to be up
echo "👁️ We're watching..."

# Cleanly wait until the port is open
until curl -s http://127.0.0.1:8188 >/dev/null; do
    sleep 1
done
echo "✅ ComfyUI server is ready."

# Start the Python watcher
"$PYTHON_BIN" watch_input_and_run_linux.py
