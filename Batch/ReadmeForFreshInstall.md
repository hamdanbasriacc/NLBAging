# 🧠 ComfyUI CLI — Headless Workflow Runner

Run ComfyUI workflows without launching the GUI — perfect for automation, pipelines, and team collaboration.

---

## 📦 Project Structure

ComfyUI-CLI/ – Root folder

comfy/ – Core ComfyUI modules

user/

default/

workflows/

aging_workflow.json – The aging workflow

output/ – Output images are saved here

input/ – Place input images here

venv/ – Python virtual environment

requirements.txt – Python dependencies list

headless_api_runner.py – Main headless runner script

setup_venv_and_install.bat – One-click setup for fresh machines

run_comfyui.bat – (Optional) GUI mode launcher

README.md – Project documentation (this file)


---

## 🧰 Prerequisites

- Windows OS
- Python 3.10 or 3.11 installed  
  ✅ **Make sure to check** "Add Python to PATH" during install  
  📥 [Download Python](https://www.python.org/downloads/)

- NVIDIA GPU with CUDA 12.8+ driver  
  (Check with: `nvidia-smi` in command prompt)

---

## 🛠️ Setup (First Time Only)

1. **Run Setup Script**

Double-click or run from terminal:

setup_venv_and_install.bat

What it does:
- Creates a `venv` (virtual environment)
- Installs Python dependencies inside the venv

---

## 🚀 Running the Workflow (Headless)

Run this from the root directory:

venv\Scripts\python.exe headless_api_runner.py


It will:
1. Start ComfyUI as a background server
2. Wait for API to become available
3. Submit `aging_workflow.json`
4. Save the output image(s) in `output/`

> 🖼️ Make sure the input image (e.g., `Female_lightskin_shorthair.png`) is placed correctly and referenced in the workflow.

---

## 🧪 Example Output Folder

After successful run:

output/
├── ComfyUI_00001_.png
├── ComfyUI_00002_.png


---

## 🛠️ Customization

- Want to run a different workflow?
  - Replace the contents of `user/default/workflows/aging_workflow.json`
  - Or edit `headless_api_runner.py` to point to a different file

- Want to launch the GUI version of ComfyUI?
  - Run `run_comfyui.bat`

---

## 📤 Sharing With Your Team

To share this setup:

1. Zip the entire `ComfyUI-CLI` folder
2. Have teammates extract it anywhere
3. They just need to run:

setup_venv_and_install.bat

arduino
Copy
Edit

Then run:

venv\Scripts\python.exe headless_api_runner.py


---

## 🧯 Troubleshooting

| Issue | Solution |
|-------|----------|
| `torch` or `DLL` errors | Make sure correct CUDA driver is installed |
| No output image | Check the input image name/path in workflow |
| Server refused connection | Ensure port 8188 is not in use |
| "Bad linked input" errors | Fix or re-export workflow via GUI first |
| Long install time | Enable Long Path support in Windows settings |

---

## 🤝 Credits

- ComfyUI: https://github.com/comfyanonymous/ComfyUI
- Wrapper scripts: customized for headless CLI automation

---

Happy inferencing! 🎉