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

# Install requirements
pip install --quiet --disable-pip-version-check -r LinuxOS/requirements.txt

# Start ComfyUI server in background
echo "🚀 Starting ComfyUI server..."
nohup venv/bin/python main.py > LinuxOS/comfyui.log 2>&1 &

# Wait a few seconds to allow server to start
sleep 3

# Start watcher
echo "👁️ Launching watcher..."
python LinuxOS/watch_input_and_run_linux.py
