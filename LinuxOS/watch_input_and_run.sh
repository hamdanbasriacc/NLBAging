#!/bin/bash

# Set working directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFYUI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INPUT_DIR="$SCRIPT_DIR/input"
OUTPUT_DIR="$SCRIPT_DIR/output"
PYTHON_BIN="$COMFYUI_DIR/venv/bin/python"
LOG_FILE="$SCRIPT_DIR/comfyui.log"

echo "🐍 Using Python: $PYTHON_BIN"

# Install Python requirements if not already done
if [ ! -f "$COMFYUI_DIR/venv/.requirements_installed" ]; then
    echo "📦 Installing Python requirements..."
    "$PYTHON_BIN" -m pip install --upgrade pip
    "$PYTHON_BIN" -m pip install -r "$COMFYUI_DIR/requirements.txt"
    touch "$COMFYUI_DIR/venv/.requirements_installed"
else
    echo "✅ Python requirements already installed."
fi

# Kill any existing ComfyUI server on port 8188
PID_ON_8188=$(lsof -ti:8188)
if [ -n "$PID_ON_8188" ]; then
    echo "⚠️ Port 8188 in use. Killing existing process (PID: $PID_ON_8188)..."
    kill -9 $PID_ON_8188
fi

# Launch ComfyUI server in background and log output
echo "🚀 Starting ComfyUI server..."
cd "$COMFYUI_DIR"
"$PYTHON_BIN" main.py --disable-auto-launch > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
cd "$SCRIPT_DIR"

# Launch watcher
echo "👁️ Launching watcher..."
"$PYTHON_BIN" watch_input_and_run_linux.py &

# Wait indefinitely for ComfyUI server to become ready
echo -n "⏳ Waiting for ComfyUI server to be ready..."
until curl -s http://127.0.0.1:8188 > /dev/null; do
    echo -n "."
    sleep 1
done

echo -e "\n✅ ComfyUI server is ready!"
