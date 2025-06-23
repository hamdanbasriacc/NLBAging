import os
import time
import json
import requests
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# === CONFIG ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_DIR = os.path.join(BASE_DIR, "input")
PROCESSED_DIR = os.path.join(INPUT_DIR, "processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
WORKFLOW_PATH = os.path.join(BASE_DIR, "user", "default", "workflows", "aging_workflow.json")
API_URL = "http://127.0.0.1:8188"
# ==============

# Ensure required directories exist
os.makedirs(PROCESSED_DIR, exist_ok=True)

def wait_for_server_ready(timeout=300):
    print("⏳ Waiting for ComfyUI server to be ready...")
    for _ in range(timeout):
        try:
            r = requests.get(f"{API_URL}/object_info")
            if r.ok:
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

    # Auto-wrap if needed
    if "prompt" not in data and all(isinstance(v, dict) and "class_type" in v for v in data.values()):
        data = {"prompt": data}
    elif "prompt" not in data:
        print("❌ Invalid workflow format: missing 'prompt'")
        return False

    # Update LoadImage node
    updated = False
    for node in data["prompt"].values():
        if node.get("class_type") == "LoadImage":
            node["inputs"]["image"] = image_name
            updated = True
            break

    if not updated:
        print("❌ No LoadImage node found to update.")
        return False

    print(f"🧪 Updating workflow with image: {image_name}")
    # Snapshot output folder before run
    before = set(os.listdir(OUTPUT_DIR))

    res = requests.post(f"{API_URL}/prompt", json={"prompt": data["prompt"]})
    if res.ok:
        print("✅ Workflow submitted successfully.")
    else:
        print(f"❌ Submission failed: {res.status_code} {res.text}")
        return False

    # Wait for new output file to appear
    for _ in range(120):
        time.sleep(1)
        after = set(os.listdir(OUTPUT_DIR))
        new_files = after - before
        if new_files:
            print(f"✅ Output found: {new_files.pop()}")
            return True

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
                    src = os.path.join(INPUT_DIR, image_name)
                    dst = os.path.join(PROCESSED_DIR, image_name)
                    time.sleep(2)
                    os.rename(src, dst)
                    print(f"✅ Moved to processed: {dst}")
                except Exception as e:
                    print(f"❌ Failed to move image: {e}")
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
    event_handler = InputHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
