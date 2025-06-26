#!/bin/bash

# Navigate to project root
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

echo "🐍 Using Python: $(which python)"

# Start ComfyUI server in the background
echo "🚀 Starting ComfyUI server..."
python main.py > LinuxOS/comfyui.log 2>&1 &
SERVER_PID=$!

# Function to check if ComfyUI is ready
wait_for_server() {
  local retries=60
  local count=0
  while [ $count -lt $retries ]; do
    if curl --silent http://127.0.0.1:8188/ > /dev/null; then
      return 0
    fi
    echo "⏳ Waiting for ComfyUI server to be ready... ($count/$retries)"
    sleep 1
    ((count++))
  done
  return 1
}

# Wait for the server to become ready
if wait_for_server; then
  echo "✅ ComfyUI server is ready."
else
  echo "❌ Timeout waiting for server. Check comfyui.log for details."
  exit 1
fi

# Run the watcher script
echo "👁️ Launching watcher..."
python LinuxOS/watch_input_and_run_linux.py
