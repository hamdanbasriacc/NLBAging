#!/bin/bash

echo "🌀 Aging Program is Starting..."

# Use full path to lsof to avoid PATH issues
PORT=8188
PID=$(sudo /usr/sbin/lsof -ti tcp:$PORT)

if [ -n "$PID" ]; then
    echo "🛑 Port $PORT is in use by PID(s): $PID. Killing..."
    sudo kill -9 $PID
else
    echo "✅ Port $PORT is free."
fi

# Launch ComfyUI + watcher
/home/hamdan_basri/ComfyUI/LinuxOS/watch_input_and_run.sh
