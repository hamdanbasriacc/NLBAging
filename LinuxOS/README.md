# 🧠 NLBAging - ComfyUI Installation & Setup Guide

Welcome to the **NLBAging** project, an image processing workflow built on top of **ComfyUI** with support for custom models, DeepFace integration, and cloud asset retrieval via Google Cloud Storage.

This guide will walk you through the setup in two phases:

- **Base Setup**: System packages, local Python installation, virtual environment, and core ComfyUI dependencies
- **Cloud Setup**: Google SDK, repo cloning, model retrieval, and shell preparation

---

## 🚀 Quick Setup (Run These in Order)

```bash
# 1. Clone the repo
git clone https://github.com/hamdanbasriacc/NLBAging.git
cd NLBAging/LinuxOS

# 2. Make the setup scripts executable
chmod +x setup_comfyui_base.sh
chmod +x setup_comfyui_google.sh

# 3. Run the base setup (Python, venv, ComfyUI install)
./setup_comfyui_base.sh

# 4. Run the cloud setup (SDK, repo/model fetch, workflows)
./setup_comfyui_google.sh
```

---

## 🛠️ What Each Script Does

### 🔹 `setup_comfyui_base.sh`
Installs everything needed to get ComfyUI running with GPU support and DeepFace integration:

1. Installs system-level packages (`libffi-devel`, `bzip2-devel`, `xz-devel`, `curl`, `unzip`)
2. Downloads and builds **Python 3.10.14** locally inside `~/ComfyUI/local_python`
3. Creates a **virtual environment** in `~/ComfyUI/venv`
4. Installs:
   - `requirements.txt` from ComfyUI
   - `torch`, `torchvision`, `torchaudio` (CUDA-enabled)
   - `deepface`, `tf-keras`
5. Starts ComfyUI once to confirm it works, then shuts it down

> This script will **skip** steps if they’ve already been completed!

---

### 🔹 `setup_comfyui_google.sh`
Sets up all the cloud-facing components and project-specific configs:

1. Installs and initializes the **Google Cloud SDK**
2. Clones both:
   - [`comfyanonymous/ComfyUI`](https://github.com/comfyanonymous/ComfyUI)
   - [`hamdanbasriacc/NLBAging`](https://github.com/hamdanbasriacc/NLBAging)
3. Downloads models from **Google Cloud Storage** into:
   - `ComfyUI/models/loras/`
   - `ComfyUI/models/checkpoints/`
4. Copies:
   - `LinuxOS/` scripts into `~/ComfyUI/LinuxOS`
   - Workflows into `~/ComfyUI/user/workflows`
5. Sets the `reset_and_run.sh` and `watch_input_and_run.sh` scripts as executable

> This script also includes smart checks to skip re-downloading anything that’s already in place.

---

## 📂 Directory Structure After Setup

```
~/ComfyUI/
├── local_python/
├── venv/
├── models/
│   ├── loras/
│   └── checkpoints/
├── LinuxOS/
│   ├── reset_and_run.sh
│   └── watch_input_and_run.sh
├── user/
│   └── workflows/
```

---

## ✅ Final Step: Run the App

Once both scripts finish, you can launch ComfyUI like this:

```bash
cd ~/ComfyUI/LinuxOS
./reset_and_run.sh
```

This will:
- Start ComfyUI
- Monitor for input images
- Process them using the configured workflow and models

---

## 🔁 Notes

- Make sure your system has CUDA drivers installed if you're using GPU.
- You can re-run either script safely. They check what’s already installed and skip duplicates.
- If you're using a different user (not `admin`), update hardcoded paths in the scripts or refactor with `$HOME`.

---

## About latest_aged_url.txt

- This file is set up by NLB Video Stitching Program and will automatically create a `latest_aged_url.txt` if its not yet available in the `shared_comfy_data` folder.
- It will pull the data and set a presigned URL.
- The URL will be stored into an array and each image will have its own presigned URL destination.

## Timeout Issues
When installing, you will face a timeout in 10minutes. The process is being downloaded & installed in the background so it should work. Sign back in and check if the process is completed.

✅ Check logs after reconnect like this:
```bash
cat ~/setup_base.log | tail -n 50   # Last 50 lines of base setup
cat ~/setup_google.log | tail -n 50 # Last 50 lines of google setup
```

Or check if something failed:

grep "error" ~/setup_base.log


## Common Commands
**`Run the program`**
```bash
cd ComfyUI/LinuxOS &&./reset_and_run.sh
```

**`Pull repo updates`**
```bash
cd
cd NLBAging
git pull
```

**`Copy files to LinuxOS`**
```bash
cp -r ~/NLBAging/LinuxOS/* ~/ComfyUI/LinuxOS/
```

**`Copy workflow`**
```bash
cp -r ~/NLBAging/workflows ~/ComfyUI/user/
```

**`Check for existing images in shared_comfy_data folder`**
```bash
ls -lah /home/admin/shared_comfy_data
```

**`Remove all images from shared_comfy_data folder`**
```bash
rm -f /home/admin/shared_comfy_data/*.{jpg,jpeg,png}
```

## Testing (Requires Two Terminals)
Terminal 1: To run 
```bash
cd ComfyUI/LinuxOS &&./reset_and_run.sh
```
Terminal 2: To copy

```bash
cp /home/admin/ComfyUI/user/workflows/Male_ticket-001.jpg /home/admin/shared_comfy_data/

cp /home/admin/ComfyUI/user/workflows/Male_ticket-002.jpeg /home/admin/shared_comfy_data/

cp /home/admin/ComfyUI/user/workflows/Male_ticket-003.jpg /home/admin/shared_comfy_data/

cp /home/admin/ComfyUI/user/workflows/Female_ticket-001.jpg /home/admin/shared_comfy_data/

cp /home/admin/ComfyUI/user/workflows/Female_ticket-002.jpg /home/admin/shared_comfy_data/
```




