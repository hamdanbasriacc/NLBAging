#!/bin/bash

# Navigate to project root
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

echo "🐍 Using Python: $(which python)"

# Check if requirements are installed (basic check via `safetensors`)
if ! python -c "import safetensors" &>/dev/null; then
  echo "📦 Installing required Python packages..."
  pip install --quiet --disable-pip-version-check -r LinuxOS/requirements.txt
else
  echo "✅ Python requirements already installed."
fi

# Start ComfyUI server in background
echo "🚀 Starting ComfyUI server..."
nohup python main.py > LinuxOS/comfyui.log 2>&1 &

# Wait for server readiness with clean line overwrite
echo -n "⏳ Waiting for ComfyUI server to be ready..."
for i in {1..60}; do
  sleep 1
  if curl -s http://127.0.0.1:8188/queue/status &>/dev/null; then
    echo -e "\r✅ ComfyUI server is ready.                     "
    break
  else
    echo -ne "\r⏳ Waiting for ComfyUI server to be ready... (${i}/60)"
  fi
done

# If timeout
if ! curl -s http://127.0.0.1:8188/queue/status &>/dev/null; then
  echo -e "\n❌ Timeout waiting for server. Check LinuxOS/comfyui.log for details."
  exit 1
fi

# Launch watcher
echo "👁️ Launching watcher..."
python LinuxOS/watch_input_and_run_linux.py
