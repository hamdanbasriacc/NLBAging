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

# Kill existing ComfyUI server on port 8188
if lsof -i:8188 -sTCP:LISTEN -t >/dev/null ; then
    echo "🛑 Existing ComfyUI server detected on port 8188. Terminating..."
    pkill -f "main.py"
    sleep 2
fi

# Check if requirements already installed
if [ ! -f "$COMFYUI_DIR/venv/.requirements_installed" ]; then
    echo "📦 Installing Python requirements..."
    "$PYTHON_BIN" -m pip install --upgrade pip
    "$PYTHON_BIN" -m pip install -r "$COMFYUI_DIR/requirements.txt"
    touch "$COMFYUI_DIR/venv/.requirements_installed"
else
    echo "✅ Python requirements already installed."
fi

# Launch ComfyUI server in the foreground so logs show in terminal
cd "$COMFYUI_DIR"
echo "🚀 Starting ComfyUI server..."
"$PYTHON_BIN" main.py --disable-auto-launch &

# Launch the Python watcher
cd "$SCRIPT_DIR"
echo "👁️ We're watching..."
"$PYTHON_BIN" watch_input_and_run_linux.py
