#!/usr/bin/env python3

import os
import time
import json
import threading
import requests
import unicodedata
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

INPUT_DIR = "/home/shared_comfy_data"
OUTPUT_DIR = "/home/hamdan_basri/ComfyUI/output"
WORKFLOW_PATH = "/home/hamdan_basri/ComfyUI/user/workflows/aging_workflow.json"
COMFYUI_API_URL = "http://127.0.0.1:8188/prompt"
STABILITY_WAIT = 2  # seconds

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_filename(filename):
    # Extract everything starting from 'ticket-' to keep UUID
    match = re.search(r'(ticket-[a-zA-Z0-9\\-_.]+)', filename, re.IGNORECASE)
    if match:
        return match.group(1)
    # fallback: remove gender prefix if any
    lower = filename.lower()
    if lower.startswith("male_") or lower.startswith("female_"):
        return filename.split("_", 1)[-1]
    return filename

def safe_filename(name):
    try:
        return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    except Exception:
        return "output_image.jpg"

def wait_for_comfyui_server(timeout=300):
    print("\u23f3 Waiting for ComfyUI server to be ready...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get("http://127.0.0.1:8188")
            if r.status_code in (200, 404):
                print("\u2705 ComfyUI server is ready.")
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("\u274c Timeout waiting for ComfyUI server.")
    exit(1)

def detect_gender_from_filename(filename):
    lower = filename.lower()
    if "female" in lower or "woman" in lower:
        return "woman"
    elif "male" in lower or "man" in lower:
        return "man"
    return None

def is_valid_image(path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception as e:
        print(f"\u26a0\ufe0f Invalid image: {path} — {e}")
        return False

def update_workflow(image_name):
    image_path = os.path.join(INPUT_DIR, image_name)
    gender = detect_gender_from_filename(image_name)

    if gender:
        print(f"\U0001f9e0 Detected gender: {gender}")
    else:
        print("\U0001f9e0 Gender not detected — no changes to prompt")

    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    for node in workflow.values():
        if isinstance(node, dict) and node.get("class_type") == "LoadImage":
            if "inputs" in node and "image" in node["inputs"]:
                node["inputs"]["image"] = image_path
        elif node.get("class_type") == "CLIPTextEncode":
            if "inputs" in node and "text" in node["inputs"]:
                prompt_text = node["inputs"]["text"]
                if isinstance(prompt_text, str) and "{gender}" in prompt_text and gender:
                    node["inputs"]["text"] = prompt_text.replace("{gender}", gender)

    return {"prompt": workflow}

def send_image(image_name):
    prompt = update_workflow(image_name)
    try:
        response = requests.post(COMFYUI_API_URL, json=prompt)
        if response.status_code == 200:
            print(f"\u2705 Submitted workflow for {image_name}")
            return True
        else:
            print(f"\u274c Submission failed: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"\u26a0\ufe0f Request failed: {e}")
        return False

def wait_for_output_and_rename(input_filename):
    print(f"\ud83d\udd0d Waiting for output for: {input_filename}")
    prev_files = set(os.listdir(OUTPUT_DIR))
    for _ in range(300):
        time.sleep(1)
        current_files = set(os.listdir(OUTPUT_DIR))
        new_files = current_files - prev_files
        candidates = [f for f in new_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if candidates:
            output_file = candidates[0]
            src = os.path.join(OUTPUT_DIR, output_file)
            cleaned_name = safe_filename(clean_filename(input_filename))
            dst = os.path.join(OUTPUT_DIR, cleaned_name)

            try:
                os.rename(src, dst)
                os.remove(os.path.join(INPUT_DIR, input_filename))
                print(f"\u2705 Renamed output as {cleaned_name} and deleted input image.")
                return
            except Exception as e:
                print(f"\u26a0\ufe0f Failed during rename/delete: {e}")
                return
    print(f"\u26a0\ufe0f Output timeout for: {input_filename}")

class InputImageHandler(FileSystemEventHandler):
    def __init__(self):
        self.queue = []
        self.processing = False

    def on_created(self, event):
        self._handle_file(event)

    def on_modified(self, event):
        self._handle_file(event)

    def _handle_file(self, event):
        if event.is_directory:
            return

        filename = os.path.basename(event.src_path)

        try:
            filename.encode('utf-8')
        except UnicodeEncodeError:
            print(f"\u26a0\ufe0f Skipping file with problematic filename: {filename}")
            return

        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return

        if filename not in self.queue:
            self.queue.append(filename)
            print(f"📸 New or updated image queued: {filename}")
            self.process_next()
        else:
            print(f"♻️ File {filename} already in queue, re-queueing due to overwrite.")
            self.queue.remove(filename)
            self.queue.append(filename)

    def process_next(self):
        if self.processing:
            return
        if not self.queue:
            return

        self.processing = True
        while self.queue:
            image_name = self.queue.pop(0)
            input_path = os.path.join(INPUT_DIR, image_name)
            print(f"🚀 Processing: {image_name}")

            for _ in range(30):
                if os.path.exists(input_path):
                    break
                time.sleep(STABILITY_WAIT)
            else:
                print(f"\u26a0\ufe0f Skipping missing input file: {input_path}")
                continue

            stable = False
            for _ in range(30):
                size1 = os.path.getsize(input_path)
                time.sleep(STABILITY_WAIT)
                size2 = os.path.getsize(input_path)
                if size1 == size2:
                    stable = True
                    break
            if not stable:
                print(f"\u26a0\ufe0f File did not stabilize: {input_path}")
                continue

            if not is_valid_image(input_path):
                continue

            if send_image(image_name):
                wait_for_output_and_rename(image_name)

        self.processing = False

def retry_queue(handler):
    while True:
        if not handler.processing and handler.queue:
            handler.process_next()
        time.sleep(5)

if __name__ == "__main__":
    print(f"👀 Watching input: {INPUT_DIR}")
    print(f"👀 Watching output: {OUTPUT_DIR}")
    observer = Observer()
    handler = InputImageHandler()
    observer.schedule(handler, INPUT_DIR, recursive=False)
    observer.start()

    wait_for_comfyui_server()

    existing_images = [f for f in os.listdir(INPUT_DIR)
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if existing_images:
        handler.queue.extend(existing_images)
        handler.process_next()

    threading.Thread(target=retry_queue, args=(handler,), daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
