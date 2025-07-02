#!/bin/bash

LOG_FILE="comfyui_log.txt"
WATCHER_SCRIPT="./watch_input_and_run.sh"

echo "🌀 Aging Program is Starting..."

# Start the watcher script in the background with logging
nohup $WATCHER_SCRIPT > "$LOG_FILE" 2>&1 &

# Wait for the "ComfyUI server is ready." message
while ! grep -q "ComfyUI server is ready." "$LOG_FILE"; do
    sleep 1
done

echo "✅ Aging Program is Ready."
