#!/bin/bash

# Navigate to project root
cd "$(dirname "$0")/.."

# Create venv if not exists
if [ ! -d "venv" ]; then
  echo "⚙️ Creating virtual environment..."
  python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "🐍 Using Python: $(which python)"

# Upgrade pip
pip install --upgrade pip

# Install core dependencies including CUDA-compatible torch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install other requirements
pip install -r LinuxOS/requirements.txt

# Start ComfyUI server with GPU in background and log output
echo "🚀 Starting ComfyUI server..."
nohup python main.py > LinuxOS/comfyui.log 2>&1 &

# Wait until server is actually ready
echo "⏳ Waiting for ComfyUI server to be ready..."
RETRIES=60
for i in $(seq 1 $RETRIES); do
  if curl -s http://127.0.0.1:8188 > /dev/null; then
    echo "✅ ComfyUI server is ready."
    break
  fi
  sleep 1
done

if [ $i -eq $RETRIES ]; then
  echo "❌ Timeout waiting for server."
  exit 1
fi

# Launch watcher
echo "👁️ Launching watcher..."
python LinuxOS/watch_input_and_run_linux.py
