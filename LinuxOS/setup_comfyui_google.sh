#!/bin/bash

set -e

echo "☁️ Checking for Google Cloud SDK..."
if [ -d "$HOME/google-cloud-sdk" ]; then
    echo "✅ Google Cloud SDK already installed, skipping download."
else
    echo "⬇️ Installing Google Cloud SDK..."
    cd ~
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-471.0.0-linux-x86_64.tar.gz
    tar -xzf google-cloud-cli-471.0.0-linux-x86_64.tar.gz
    ./google-cloud-sdk/install.sh
fi

echo "📤 Setting up Google Cloud environment..."
source "$HOME/google-cloud-sdk/path.bash.inc"

if ! gcloud config list account --quiet &>/dev/null; then
    echo "⚙️ Running gcloud init..."
    gcloud init
else
    echo "✅ gcloud already initialized, skipping."
fi

echo "🐙 Cloning repositories..."
cd ~
if [ ! -d "ComfyUI" ]; then
    git clone https://github.com/comfyanonymous/ComfyUI.git
else
    echo "✅ 'ComfyUI' repo already cloned."
fi

if [ ! -d "NLBAging" ]; then
    git clone https://github.com/hamdanbasriacc/NLBAging.git
else
    echo "✅ 'NLBAging' repo already cloned."
fi

echo "☁️ Downloading GCS models if not already present..."
mkdir -p /home/admin/ComfyUI/models/loras /home/admin/ComfyUI/models/checkpoints

if [ ! -f "/home/admin/ComfyUI/models/loras/bodygrammps.pt" ]; then
    gsutil cp gs://public-bucket-gdcc-setup/workflow/bodygrammps.pt /home/admin/ComfyUI/models/loras/
else
    echo "✅ bodygrammps.pt already exists."
fi

if [ ! -f "/home/admin/ComfyUI/models/checkpoints/cyberrealistic-dreambooth.safetensors" ]; then
    gsutil cp gs://public-bucket-gdcc-setup/workflow/cyberrealistic-dreambooth.safetensors /home/admin/ComfyUI/models/checkpoints/
else
    echo "✅ cyberrealistic-dreambooth.safetensors already exists."
fi

echo "📁 Copying LinuxOS files..."
mkdir -p ~/ComfyUI/LinuxOS
cp -ru ~/NLBAging/LinuxOS/* ~/ComfyUI/LinuxOS/

echo "📁 Copying workflows..."
mkdir -p ~/ComfyUI/user
cp -ru ~/NLBAging/workflows ~/ComfyUI/user/

echo "🔑 Making shell scripts executable..."
chmod +x /home/admin/ComfyUI/LinuxOS/reset_and_run.sh
chmod +x /home/admin/ComfyUI/LinuxOS/watch_input_and_run.sh

echo "✅ Google Cloud setup and project files are ready!"
