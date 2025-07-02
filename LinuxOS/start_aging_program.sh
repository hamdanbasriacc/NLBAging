#!/bin/bash

echo "🌀 Aging Program is Starting..."

# Check if port 8188 is in use and kill the process
PORT=8188
PID=$(lsof -ti tcp:$PORT)
if [ -n "$PID" ]; then
    echo "🛑 Port $PORT is in use by PID $PID. Killing..."
    kill -9 $PID
fi

# Launch script
./watch_input_and_run.sh
