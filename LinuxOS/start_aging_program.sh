#!/bin/bash

echo "🌀 Aging Program is Starting..."

PORT=8188
PID=$(lsof -ti tcp:$PORT)

if [ -n "$PID" ]; then
    echo "🛑 Port $PORT is in use by PID(s): $PID. Killing..."
    kill -9 $PID
else
    echo "✅ Port $PORT is free."
fi

# Launch ComfyUI + watcher
./watch_input_and_run.sh
