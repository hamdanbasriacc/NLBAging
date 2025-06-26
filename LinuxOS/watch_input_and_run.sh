#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFYUI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INPUT_DIR="$SCRIPT_DIR/input"
OUTPUT_DIR="$SCRIPT_DIR/output"
PYTHON_BIN="$COMFYUI_DIR/venv/bin/python"

echo "🐍 Using Python: $PYTHON_BIN"

# Install requirements only once
if [ ! -f "$COMFYUI_DIR/venv/.requirements_installed" ]; then
    echo "📦 Installing Python requirements..."
    "$PYTHON_BIN" -m pip install --upgrade pip
    "$PYTHON_BIN" -m pip install -r "$COMFYUI_DIR/requirements.txt"
    touch "$COMFYUI_DIR/venv/.requirements_installed"
else
    echo "✅ Python requirements already installed."
fi

# Start watcher in background
echo "👁️ We're watching..."
"$PYTHON_BIN" "$SCRIPT_DIR/watch_input_and_run_linux.py" &

# Run ComfyUI server in foreground (logs will be visible in this terminal)
cd "$COMFYUI_DIR"
"$PYTHON_BIN" main.py --disable-auto-launch
