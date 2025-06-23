import os
import time
import json
import requests
import subprocess
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread

# === CONFIG ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_DIR = os.path.join(BASE_DIR, "input")
PROCESSED_DIR = os.path.join(INPUT_DIR, "processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
WORKFLOW_PATH = os.path.join(BASE_DIR, "user", "default", "workflows", "aging_workflow.json")
API_URL = "http://127.0.0.1:8188"
DEFAULT_OUTPUT_PREFIX = "ComfyUI_"
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
        print("❌ Invalid workflow format.")
        return False

    updated = False
    for node in data["prompt"].values():
        if node.get("class_type") == "LoadImage":
            node["inputs"]["image"] = image_name
            updated = True
            break

    if not updated:
        print("❌ No LoadImage node found.")
        return False

    print(f"🧪 Updating workflow with image: {image_name}")
    res = requests.post(f"{API_URL}/prompt", json={"prompt": data["prompt"]})
    if res.ok:
        print(f"✅ Workflow submitted for {image_name}")
        return True
    print(f"❌ Workflow submission failed: {res.status_code} {res.text}")
    return False

def wait_and_rename_output(image_name, timeout=180):
    base_output_name = os.path.splitext(image_name)[0] + ".png"
    print(f"⏳ Waiting for output to rename to: {base_output_name}")
    start_time = time.time()

    seen_files = set(os.listdir(OUTPUT_DIR))
    while time.time() - start_time < timeout:
        current_files = set(os.listdir(OUTPUT_DIR))
        new_files = current_files - seen_files
        for new_file in new_files:
            if new_file.startswith(DEFAULT_OUTPUT_PREFIX) and new_file.endswith(".png"):
                src = os.path.join(OUTPUT_DIR, new_file)
                dst = os.path.join(OUTPUT_DIR, base_output_name)
                try:
                    shutil.copy2(src, dst)
                    os.remove(src)
                    print(f"✅ Output renamed to: {base_output_name}")
                    return True
                except Exception as e:
                    print(f"❌ Rename failed: {e}")
        time.sleep(1)

    print(f"❌ Timeout waiting for output of {image_name}")
    return False

class InputHandler(FileSystemEventHandler):
    def __init__(self):
        self.queue = []
        self.processing = False

    def on_created(self, event):
        if event.is_directory or not event.src_path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            return
        image_name = os.path.basename(event.src_path)
        print(f"📸 New image queued: {image_name}")
        self.queue.append(image_name)
        if not self.processing:
            Thread(target=self.process_queue).start()

    def process_queue(self):
        self.processing = True
        while self.queue:
            image_name = self.queue[0]
            if send_image_to_comfy(image_name):
                if wait_and_rename_output(image_name):
                    try:
                        src = os.path.join(INPUT_DIR, image_name)
                        dst = os.path.join(PROCESSED_DIR, image_name)
                        time.sleep(1)
                        shutil.move(src, dst)
                        print(f"✅ Moved to processed: {image_name}")
                        self.queue.pop(0)
                    except Exception as e:
                        print(f"❌ Failed to move input image: {e}")
                        break
                else:
                    print(f"❌ Skipping due to output rename failure: {image_name}")
                    break
            else:
                print(f"❌ Skipping due to submission error: {image_name}")
                break
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

    print(f"👀 Watching input: {INPUT_DIR}")
    print(f"👀 Watching output: {OUTPUT_DIR}")
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
