#!/bin/bash

set -e

echo "🔧 Installing system packages (libffi, bzip2, xz, curl, unzip)..."
sudo dnf install -y libffi-devel bzip2-devel xz-devel curl unzip

PYTHON_VERSION="3.10.14"
PYTHON_DIR="/home/admin/ComfyUI/local_python/python-3.10"
PYTHON_BIN="$PYTHON_DIR/bin/python3.10"
VENV_DIR="/home/admin/ComfyUI/venv"

echo "🐍 Checking for local Python $PYTHON_VERSION..."
if [ -x "$PYTHON_BIN" ]; then
    echo "✅ Python $PYTHON_VERSION already installed."
else
    echo "⬇️ Installing Python $PYTHON_VERSION locally..."
    cd /home/admin/ComfyUI
    mkdir -p local_python && cd local_python

    if [ ! -f "Python-$PYTHON_VERSION.tgz" ]; then
        wget "https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz"
    fi

    tar -xzf Python-$PYTHON_VERSION.tgz
    cd Python-$PYTHON_VERSION
    ./configure --prefix=$PYTHON_DIR --enable-optimizations
    make -j$(nproc)
    make install
fi

echo "🐍 Verifying Python version..."
$PYTHON_BIN --version

echo "📦 Checking for virtual environment..."
if [ -d "$VENV_DIR" ]; then
    echo "✅ Virtual environment already exists."
else
    echo "🧪 Creating virtual environment..."
    $PYTHON_BIN -m venv $VENV_DIR
fi

echo "📥 Activating virtual environment..."
source $VENV_DIR/bin/activate

echo "⬆️ Upgrading pip..."
pip install --upgrade pip

REQ_TXT="/home/admin/ComfyUI/requirements.txt"
if [ -f "$REQ_TXT" ]; then
    echo "📦 Installing Python dependencies from requirements.txt..."
    pip install -r $REQ_TXT
else
    echo "⚠️ No requirements.txt found at $REQ_TXT — skipping."
fi

echo "🔥 Installing PyTorch with CUDA..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo "🚀 Starting ComfyUI to confirm it works..."
cd /home/admin/ComfyUI
python main.py &

echo "⌛ Waiting 5 seconds before stopping ComfyUI..."
sleep 5
pkill -f "main.py"

echo "✅ Base ComfyUI setup complete!"
