#!/bin/bash

# Log everything to setup_base.log
exec > >(tee -a ~/setup_base.log) 2>&1

set -e

log_step() {
  echo -e "\n🔹 $1\n"
}

run_in_bg() {
  eval "$1" &
  wait $!
}

# STEP 1 - Install Google Cloud SDK
log_step "Step 1: Checking/installing Google Cloud SDK..."

if [ -d "$HOME/google-cloud-sdk" ]; then
  echo "✅ Google Cloud SDK already installed, skipping..."
else
  cd ~
  run_in_bg "curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-471.0.0-linux-x86_64.tar.gz"
  run_in_bg "tar -xzf google-cloud-cli-471.0.0-linux-x86_64.tar.gz"
  run_in_bg "./google-cloud-sdk/install.sh"
fi

# STEP 2 - Initialize Google SDK
log_step "Step 2: Loading and initializing gcloud..."

source "$HOME/google-cloud-sdk/path.bash.inc"

if ! gcloud config list account --quiet &>/dev/null; then
  run_in_bg "gcloud init"
else
  echo "✅ gcloud already initialized, skipping..."
fi

# STEP 3 - Clone repos
log_step "Step 3: Cloning ComfyUI and NLBAging repos..."

cd ~
[ ! -d "ComfyUI" ] && run_in_bg "git clone https://github.com/comfyanonymous/ComfyUI.git" || echo "✅ ComfyUI already cloned."
[ ! -d "NLBAging" ] && run_in_bg "git clone https://github.com/hamdanbasriacc/NLBAging.git" || echo "✅ NLBAging already cloned."

# STEP 4 - Download GCS models
log_step "Step 4: Downloading model files from Google Cloud Storage..."

mkdir -p ~/ComfyUI/models/loras ~/ComfyUI/models/checkpoints

[ ! -f ~/ComfyUI/models/loras/blindbox_v1_mix.safetensors ] && \
  run_in_bg "gsutil cp gs://public-bucket-gdcc-setup/workflow/blindbox_v1_mix.safetensors ~/ComfyUI/models/loras/" || \
  echo "✅ blindbox_v1_mix.safetensors already exists."

[ ! -f ~/ComfyUI/models/checkpoints/dreamshaper_8.safetensors ] && \
  run_in_bg "gsutil cp gs://public-bucket-gdcc-setup/workflow/dreamshaper_8.safetensors ~/ComfyUI/models/checkpoints/" || \
  echo "✅ dreamshaper_8.safetensors already exists."

# STEP 5 - Copy LinuxOS
log_step "Step 5: Copying LinuxOS scripts..."

mkdir -p ~/ComfyUI/LinuxOS
cp -ru ~/NLBAging/LinuxOS/* ~/ComfyUI/LinuxOS/

# STEP 6 - Copy workflows
log_step "Step 6: Copying workflows..."

mkdir -p ~/ComfyUI/user
cp -ru ~/NLBAging/workflows ~/ComfyUI/user/

# STEP 7 - Make scripts executable
log_step "Step 7: Setting executable permissions..."

chmod +x ~/ComfyUI/LinuxOS/reset_and_run.sh
chmod +x ~/ComfyUI/LinuxOS/watch_input_and_run.sh

echo -e "\n🎉 All setup steps completed successfully!"

touch ~/.setup_comfyui_base_done
