import os
import time
import json
import requests
import shutil
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")
PROCESSED_DIR = os.path.join(INPUT_DIR, "processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
WORKFLOW_PATH = os.path.join(BASE_DIR, "user", "default", "workflows", "aging_workflow.json")
API_URL = "http://127.0.0.1:8188/prompt"

os.makedirs(PROCESSED_DIR, exist_ok=True)

def wait_for_server(timeout=300):
    print("⏳ Waiting for ComfyUI server to be ready...")
    for _ in range(timeout):
        try:
            if requests.get("http://127.0.0.1:8188/object_info").ok:
                print("✅ ComfyUI server is ready.")
                return True
        except:
            pass
        time.sleep(1)
    print("❌ Timeout waiting for server.")
    return False

def update_workflow(image_name):
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "prompt" not in data:
        if all(isinstance(v, dict) and "class_type" in v for v in data.values()):
            data = {"prompt": data}
        else:
            print("❌ Invalid workflow structure.")
            return None

    for node in data["prompt"].values():
        if node.get("class_type") == "LoadImage":
            node["inputs"]["image"] = image_name
            break
    else:
        print("❌ LoadImage node not found.")
        return None

    return data["prompt"]

def send_image(image_name):
    print(f"🧪 Updating workflow with image: {image_name}")
    prompt = update_workflow(image_name)
    if not prompt:
        return False

    res = requests.post(API_URL, json={"prompt": prompt})
    if res.ok:
        print(f"✅ Workflow submitted for {image_name}")
        return True
    print(f"❌ Submission failed: {res.status_code} {res.text}")
    return False

def wait_and_rename_output(original_image):
    base_name = os.path.splitext(original_image)[0]
    target_name = f"{base_name}.png"
    print(f"⏳ Waiting for output to rename to: {target_name}")
    deadline = time.time() + 180

    already_seen = set(os.listdir(OUTPUT_DIR))

    while time.time() < deadline:
        current_files = set(os.listdir(OUTPUT_DIR))
        new_files = current_files - already_seen

        for new_file in new_files:
            if new_file.lower().endswith(".png"):
                src = os.path.join(OUTPUT_DIR, new_file)
                dst = os.path.join(OUTPUT_DIR, target_name)
                try:
                    shutil.copy(src, dst)
                    os.remove(src)
                    print(f"✅ Output renamed to: {target_name}")
                    return True
                except Exception as e:
                    print(f"❌ Rename failed: {e}")
        time.sleep(1)

    print(f"❌ Timeout waiting for output of {original_image}")
    return False

class Watcher(FileSystemEventHandler):
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
        self.processing = False

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            image_name = os.path.basename(event.src_path)
            print(f"📸 New image queued: {image_name}")
            with self.lock:
                self.queue.append(image_name)
            self.process_queue()

    def process_queue(self):
        if self.processing:
            return
        self.processing = True

        while self.queue:
            with self.lock:
                image_name = self.queue.pop(0)

            print(f"🚀 Processing: {image_name}")
            if send_image(image_name):
                if wait_and_rename_output(image_name):
                    src = os.path.join(INPUT_DIR, image_name)
                    dst = os.path.join(PROCESSED_DIR, image_name)
                    try:
                        os.rename(src, dst)
                        print(f"✅ Moved to processed: {image_name}")
                    except Exception as e:
                        print(f"❌ Failed to move: {e}")
        self.processing = False

if __name__ == "__main__":
    print(f"👀 Watching input: {INPUT_DIR}")
    print(f"👀 Watching output: {OUTPUT_DIR}")

    if not wait_for_server():
        exit(1)

    observer = Observer()
    handler = Watcher()
    observer.schedule(handler, INPUT_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
