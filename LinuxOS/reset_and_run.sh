#!/bin/bash

echo "🔪 Killing old processes..."
pkill -f "watch_input_and_run"
pkill -f "main.py"

echo "🔍 Checking leftover processes..."
ps aux | grep watch | grep -v grep

echo "🧹 Cleaning shared input folder..."
rm -f /home/shared_comfy_data/*.{jpg,jpeg,png}

echo "📂 Listing contents of shared input folder..."
ls -lah /home/shared_comfy_data

echo "🚀 Restarting ComfyUI watcher..."
cd /home/hamdan_basri/ComfyUI/LinuxOS && ./watch_input_and_run.sh
