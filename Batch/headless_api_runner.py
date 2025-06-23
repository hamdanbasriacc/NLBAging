import os
import time
import json
import requests
import subprocess
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# === CONFIG ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_DIR = os.path.join(BASE_DIR, "input")
PROCESSED_DIR = os.path.join(INPUT_DIR, "processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
WORKFLOW_PATH = os.path.join(BASE_DIR, "user", "default", "workflows", "aging_workflow.json")
API_URL = "http://127.0.0.1:8188"
TIMEOUT_OUTPUT = 120  # seconds
# ==============

os.makedirs(PROCESSED_DIR, exist_ok=True)

def wait_for_server_ready(timeout=300):
    print("⏳ Waiting for ComfyUI server to be ready...")
    for _ in range(timeout):
        try:
            if requests.get(f"{API_URL}/object_info").ok:
                print("✅ ComfyUI server is ready.")
                return True
        except:
            pass
        time.sleep(1)
    print("❌ Timeout waiting for server.")
    return False

def send_image_to_comfy(image_name):
    print(f"🚀 Processing: {image_name}")
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "prompt" not in data and all(isinstance(v, dict) and "class_type" in v for v in data.values()):
        data = {"prompt": data}
    elif "prompt" not in data:
        print("❌ Invalid workflow format: missing 'prompt'")
        return False

    for node in data["prompt"].values():
        if node.get("class_type") == "LoadImage":
            node["inputs"]["image"] = image_name
        if node.get("class_type") == "SaveImage":
            node["inputs"]["filename_prefix"] = os.path.splitext(image_name)[0]

    print(f"🧪 Updating workflow with image: {image_name}")
    res = requests.post(f"{API_URL}/prompt", json={"prompt": data["prompt"]})
    if res.ok:
        print("✅ Workflow submitted successfully.")
    else:
        print(f"❌ Submission failed: {res.status_code} {res.text}")
        return False

    input_stem = os.path.splitext(image_name)[0]
    start_time = time.time()

    # Wait for new output image
    existing = set(os.listdir(OUTPUT_DIR))
    while time.time() - start_time < TIMEOUT_OUTPUT:
        current = set(os.listdir(OUTPUT_DIR))
        new_files = current - existing
        for f in new_files:
            if f.endswith((".png", ".jpg", ".jpeg", ".webp")):
                src_path = os.path.join(OUTPUT_DIR, f)
                dst_name = input_stem + os.path.splitext(f)[1]
                dst_path = os.path.join(OUTPUT_DIR, dst_name)
                try:
                    shutil.copy2(src_path, dst_path)
                    print(f"✅ Output copied and renamed to: {dst_name}")
                    return True
                except Exception as e:
                    print(f"❌ Failed to copy/rename: {e}")
        time.sleep(1)

    print(f"❌ Timeout waiting for output of {image_name}")
    return False

class InputHandler(FileSystemEventHandler):
    def __init__(self):
        self.queue = []
        self.processing = False

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            image_name = os.path.basename(event.src_path)
            print(f"📸 New image queued: {image_name}")
            self.queue.append(image_name)
            if not self.processing:
                self.process_queue()

    def process_queue(self):
        self.processing = True
        while self.queue:
            image_name = self.queue.pop(0)
            if send_image_to_comfy(image_name):
                try:
                    time.sleep(2)
                    shutil.move(os.path.join(INPUT_DIR, image_name), os.path.join(PROCESSED_DIR, image_name))
                    print(f"✅ Moved to processed: {image_name}")
                except Exception as e:
                    print(f"❌ Failed to move to processed: {e}")
        self.processing = False

def start_server():
    print("🚀 Starting ComfyUI server...")
    subprocess.Popen(
        ["venv\\Scripts\\python.exe", "main.py"],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

if __name__ == "__main__":
    print("⚙️ Starting watcher and ComfyUI server...")
    start_server()
    if not wait_for_server_ready():
        exit(1)

    print(f"👀 Watching folder: {INPUT_DIR}")
    observer = Observer()
    observer.schedule(InputHandler(), INPUT_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
