#!/bin/bash

echo "🌀 Aging Program is Starting..."

# Kill any process using port 8188
if ss -ltn | grep -q ':8188'; then
    echo "🛑 Port 8188 in use, killing existing process..."
    pkill -f "main.py"
    sleep 3
else
    echo "✅ Port 8188 is free."
fi

cd "$(dirname "$0")"
./watch_input_and_run.sh
