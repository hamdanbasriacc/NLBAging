#!/bin/bash 

# Set working directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFYUI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INPUT_DIR="$SCRIPT_DIR/input"
OUTPUT_DIR="$SCRIPT_DIR/output"
PYTHON_BIN="$COMFYUI_DIR/venv/bin/python"

echo "🐍 Using Python: $PYTHON_BIN"

# Kill ComfyUI if running on port 8188 using ss and pkill fallback
if ss -ltn | grep -q ':8188'; then
    echo "🛑 Port 8188 in use, killing previous ComfyUI instance..."
    pkill -f "main.py"
    sleep 2
else
    echo "✅ Port 8188 is free."
fi

# Check if requirements are installed
if [ ! -f "$COMFYUI_DIR/venv/.requirements_installed" ]; then
    echo "📦 Installing Python requirements..."
    "$PYTHON_BIN" -m pip install --upgrade pip
    "$PYTHON_BIN" -m pip install -r "$COMFYUI_DIR/requirements.txt"
    touch "$COMFYUI_DIR/venv/.requirements_installed"
else
    echo "✅ Python requirements already installed."
fi

# Launch ComfyUI server in foreground
cd "$COMFYUI_DIR"
echo "🚀 Starting ComfyUI server..."
"$PYTHON_BIN" main.py --disable-auto-launch &

# Launch input watcher
cd "$SCRIPT_DIR"
echo "👁️ Watching for input..."
"$PYTHON_BIN" watch_input_and_run_linux.py &

# Launch output uploader watcher
echo "📤 Watching for generated outputs to upload..."
"$PYTHON_BIN" watcher_send_output.py &

# Launch auto-copy watcher from uploads folder
echo "📥 Watching for new uploads to copy into input..."
"$PYTHON_BIN" watcher_send_output.py > "$SCRIPT_DIR/watcher_output.log" 2>&1 &
