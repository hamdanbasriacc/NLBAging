#!/bin/bash

# Log everything to a file
exec > >(tee -a ~/setup_full_install.log) 2>&1
set -e

log_step() {
  echo -e "\n🔹 $1\n"
}

run_in_bg() {
  eval "$1" &
  wait $!
}

PYTHON_VERSION="3.10.14"
PYTHON_DIR="/home/admin/ComfyUI/local_python/python-3.10"
PYTHON_BIN="$PYTHON_DIR/bin/python3.10"
VENV_DIR="/home/admin/ComfyUI/venv"
SHARED_DIR="/home/admin/shared_comfy_data"
COMFYUI_DIR="/home/admin/ComfyUI"

########################################
log_step "Step 1: Checking system packages"

are_packages_missing=false
for pkg in libffi-devel bzip2-devel xz-devel curl unzip; do
  rpm -q $pkg > /dev/null 2>&1 || are_packages_missing=true
done

if $are_packages_missing; then
  log_step "Installing missing system packages..."
  sudo dnf install -y libffi-devel bzip2-devel xz-devel curl unzip
else
  echo "✅ All required system packages already installed."
fi

########################################
log_step "Step 2: Preparing ComfyUI folder (cloning repo)"
if [ ! -d "$COMFYUI_DIR/.git" ]; then
  echo "📦 Cloning ComfyUI into $COMFYUI_DIR..."
  git clone https://github.com/comfyanonymous/ComfyUI.git $COMFYUI_DIR
else
  echo "✅ ComfyUI already cloned."
fi
cd $COMFYUI_DIR

########################################
log_step "Step 3: Installing Python $PYTHON_VERSION"
if [ -x "$PYTHON_BIN" ]; then
  echo "✅ Python $PYTHON_VERSION already installed."
else
  mkdir -p local_python && cd local_python
  [ ! -f "Python-$PYTHON_VERSION.tgz" ] && run_in_bg "wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz"
  tar -xzf Python-$PYTHON_VERSION.tgz
  cd Python-$PYTHON_VERSION
  run_in_bg "./configure --prefix=$PYTHON_DIR --enable-optimizations"
  run_in_bg "make -j$(nproc)"
  run_in_bg "make install"
fi

########################################
log_step "Step 4: Verifying Python version"
$PYTHON_BIN --version | grep "$PYTHON_VERSION"

########################################
log_step "Step 5: Creating virtual environment"
if [ -d "$VENV_DIR" ]; then
  echo "✅ Virtual environment already exists."
else
  run_in_bg "$PYTHON_BIN -m venv $VENV_DIR"
fi
source $VENV_DIR/bin/activate

########################################
log_step "Step 6: Installing ComfyUI dependencies"
pip install --upgrade pip
[ -f "$COMFYUI_DIR/requirements.txt" ] && pip install -r "$COMFYUI_DIR/requirements.txt"
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

########################################
log_step "Step 7: Installing DeepFace + tf-keras"
python -c "import deepface" &>/dev/null || run_in_bg "pip install deepface"
python -c "import tf_keras" &>/dev/null || run_in_bg "pip install tf-keras"

########################################
log_step "Step 8: Running ComfyUI once"
cd $COMFYUI_DIR
python main.py &
sleep 5
pkill -f "main.py"

########################################
log_step "Step 9: Installing Google Cloud SDK"
if [ ! -d "$HOME/google-cloud-sdk" ]; then
  cd ~
  run_in_bg "curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-471.0.0-linux-x86_64.tar.gz"
  run_in_bg "tar -xzf google-cloud-cli-471.0.0-linux-x86_64.tar.gz"
  run_in_bg "./google-cloud-sdk/install.sh"
fi

########################################
log_step "Step 10: Initializing gcloud"
source "$HOME/google-cloud-sdk/path.bash.inc"
if ! gcloud config list account --quiet &>/dev/null; then
  run_in_bg "gcloud init"
fi

########################################
log_step "Step 11: Cloning NLBAging"
cd ~

########################################
log_step "Step 12: Downloading models from GCS"
mkdir -p ~/ComfyUI/models/loras ~/ComfyUI/models/checkpoints
[ ! -f ~/ComfyUI/models/loras/blindbox_v1_mix.safetensors ] &&   run_in_bg "gsutil cp gs://public-bucket-gdcc-setup/workflow/blindbox_v1_mix.safetensors ~/ComfyUI/models/loras/"
[ ! -f ~/ComfyUI/models/checkpoints/dreamshaper_8.safetensors ] &&   run_in_bg "gsutil cp gs://public-bucket-gdcc-setup/workflow/dreamshaper_8.safetensors ~/ComfyUI/models/checkpoints/"

########################################
log_step "Step 13: Copying LinuxOS scripts"
mkdir -p ~/ComfyUI/LinuxOS
cp -ru ~/NLBAging/LinuxOS/* ~/ComfyUI/LinuxOS/

########################################
log_step "Step 14: Copying workflow files"
mkdir -p ~/ComfyUI/user
cp -ru ~/NLBAging/workflows ~/ComfyUI/user/

########################################
log_step "Step 15: Setting up shared_comfy_data folder"
if [ ! -d "$SHARED_DIR" ]; then
  run_in_bg "mkdir -p $SHARED_DIR"
  run_in_bg "chown admin:admin $SHARED_DIR"
  run_in_bg "chmod 755 $SHARED_DIR"
fi
if [ ! -f "$SHARED_DIR/latest_aged_url.txt" ]; then
  cp ~/NLBAging/workflows/latest_aged_url.txt $SHARED_DIR/
fi

########################################
log_step "Step 16: Setting script permissions"
chmod +x ~/ComfyUI/LinuxOS/reset_and_run.sh
chmod +x ~/ComfyUI/LinuxOS/watch_input_and_run.sh

########################################
log_step "Step 17: Starting ComfyUI"
cd ~/ComfyUI/LinuxOS
./reset_and_run.sh &

echo -e "\n🎉 All setup steps completed successfully!"
touch ~/.setup_comfyui_full_done
