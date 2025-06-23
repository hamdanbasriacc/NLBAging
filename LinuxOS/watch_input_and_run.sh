#!/bin/bash

# Navigate to project root
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Optional: Confirm virtualenv
echo "🐍 Using Python: $(which python)"

# Run the unified watcher and server script
echo "🚀 Launching watcher and ComfyUI server..."
python LinuxOS/watch_input_and_run_linux.py
