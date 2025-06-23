#!/bin/bash

# Navigate to the root project directory
cd "$(dirname "$0")/.."

# Activate the virtual environment
source venv/bin/activate

echo "🚀 Starting ComfyUI server..."
# Start ComfyUI in the background and save its PID
python main.py > /dev/null 2>&1 &
COMFY_PID=$!

# Function to clean up on exit
cleanup() {
    echo "🛑 Shutting down..."
    kill $COMFY_PID
    exit
}
trap cleanup SIGINT SIGTERM

# Wait for the server to be ready
echo "⏳ Waiting for ComfyUI server to be ready..."
for i in {1..300}; do
    if curl -s http://127.0.0.1:8188/object_info > /dev/null; then
        echo "✅ ComfyUI server is ready."
        break
    fi
    sleep 1
done

if ! curl -s http://127.0.0.1:8188/object_info > /dev/null; then
    echo "❌ Server did not start within timeout. Exiting."
    kill $COMFY_PID
    exit 1
fi

# Start the watcher
echo "👀 Starting image input watcher..."
python LinuxOS/watch_input_and_run_linux.py

# When done, clean up
cleanup
