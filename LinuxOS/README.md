# 🐧 Linux Headless Workflow Watcher for ComfyUI

This setup watches the `input/` folder for new images and automatically runs the headless ComfyUI workflow on them.

## 📂 Directory Structure

C:/ComfyUI-CLI/
├── LinuxOS/
│ ├── watch_input_and_run_linux.py
│ ├── requirements.txt
│ └── README.md
├── input/ # Drop your images here
├── output/ # Generated images will appear here
├── user/
│ └── default/
│ └── workflows/
│ └── aging_workflow.json
└── venv/ # Python virtual environment

bash
Copy
Edit

## 🧰 Requirements

- Python 3.10+
- ComfyUI set up in the root of `C:/ComfyUI-CLI`
- Virtual environment activated (`source venv/bin/activate`)

## 🚀 Setup Instructions

1. **Activate the virtual environment:**

cd /mnt/c/ComfyUI-CLI
source venv/bin/activate

2. **Install dependencies:**

pip install -r LinuxOS/requirements.txt

3. **Run the watcher:**

python LinuxOS/watch_input_and_run_linux.py


The script will start the ComfyUI server, wait for it to be ready, and monitor the input/ folder for image files. Once an image is detected, it updates the LoadImage node in the workflow and submits it.

The output will be saved in output/, and the input image will be moved to input/processed/ only after output is confirmed.