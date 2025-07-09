#!/usr/bin/env python3

import os
import time
import json
import requests
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# === Config ===
INPUT_DIR = "/home/shared_comfy_data"
OUTPUT_DIR = "/home/hamdan_basri/ComfyUI/output"
WORKFLOW_PATH = "/home/hamdan_basri/ComfyUI/user/workflows/aging_workflow.json"
COMFYUI_API_URL = "http://127.0.0.1:8188/prompt"
TARGET_URL_FILE = "/home/shared_comfy_data/latest_aged_url.txt"
STABILITY_WAIT = 2  # seconds
UPLOAD_TIMEOUT = 5  # seconds for upload retry wait

# === Logging Setup ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Ensure Directories Exist ===
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === ComfyUI Wait ===
def wait_for_comfyui_server(timeout=300):
    print("⏳ Waiting for ComfyUI server to be ready...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get("http://127.0.0.1:8188")
            if r.status_code in (200, 404):
                print("✅ ComfyUI server is ready.")
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("❌ Timeout waiting for ComfyUI server.")
    exit(1)

# === Gender Detection ===
def detect_gender_from_filename(filename):
    lower = filename.lower()
    if "female" in lower or "woman" in lower:
        return "woman"
    elif "male" in lower or "man" in lower:
        return "man"
    return None

# === Workflow Preparer ===
def update_workflow(image_name):
    image_path = os.path.join(INPUT_DIR, image_name)
    gender = detect_gender_from_filename(image_name)

    if gender:
        print(f"🧠 Detected gender: {gender}")
    else:
        print("🧠 Gender not detected — no changes to prompt")

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

# === Target URL Reader ===
def get_target_url():
    try:
        with open(TARGET_URL_FILE, "r") as f:
            url = f.read().strip()
            if url:
                return url
    except Exception as e:
        logging.warning(f"⚠️ Failed to read target URL: {e}")
    return None

# === Upload Handler ===
def is_file_stable(filepath):
    try:
        size1 = os.path.getsize(filepath)
        time.sleep(STABILITY_WAIT)
        size2 = os.path.getsize(filepath)
        return size1 == size2
    except Exception:
        return False

def upload_image(image_path, target_url):
    try:
        with open(image_path, "rb") as img:
            headers = {"Content-Type": "image/jpeg"}
            response = requests.put(target_url, data=img, headers=headers)
        if response.status_code in [200, 201]:
            logging.info(f"✅ Uploaded: {os.path.basename(image_path)}")
            return True
        else:
            logging.warning(f"❌ Upload failed: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"❌ Exception during upload: {e}")
    return False

# === Image Submission + Output Wait + Upload + Cleanup ===
def send_image(image_name):
    prompt = update_workflow(image_name)
    try:
        response = requests.post(COMFYUI_API_URL, json=prompt)
        if response.status_code == 200:
            print(f"✅ Submitted workflow for {image_name}")
            return True
        else:
            print(f"❌ Submission failed: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"⚠️ Request failed: {e}")
        return False

def wait_for_output_rename_and_upload(input_filename):
    print(f"🔍 Waiting for output for: {input_filename}")
    prev_files = set(os.listdir(OUTPUT_DIR))
    for _ in range(300):
        time.sleep(1)
        current_files = set(os.listdir(OUTPUT_DIR))
        new_files = current_files - prev_files
        candidates = [f for f in new_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if candidates:
            output_file = candidates[0]
            src = os.path.join(OUTPUT_DIR, output_file)
            dst = os.path.join(OUTPUT_DIR, input_filename)

            try:
                if not is_file_stable(src):
                    logging.info(f"⏳ Output not stable yet: {output_file}")
                    return

                # Rename output to match input filename
                with open(src, "rb") as fsrc:
                    content = fsrc.read()
                with open(dst, "wb") as fdst:
                    fdst.write(content)
                os.remove(src)
                print(f"📄 Renamed output to: {input_filename}")

                # Upload renamed file
                target_url = get_target_url()
                if not target_url:
                    logging.warning("⚠️ No presigned URL found — skipping upload")
                    return

                if upload_image(dst, target_url):
                    os.remove(dst)
                    os.remove(os.path.join(INPUT_DIR, input_filename))
                    logging.info(f"🗑️ Cleaned up {input_filename} after successful upload")
                else:
                    logging.warning(f"❌ Upload failed — keeping files for retry")

                return
            except Exception as e:
                print(f"⚠️ Failed during output handling: {e}")
                return

# === File Watcher ===
class InputImageHandler(FileSystemEventHandler):
    def __init__(self):
        self.queue = []
        self.processing = False

    def on_created(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            if filename not in self.queue:
                self.queue.append(filename)
                print(f"📸 New image queued: {filename}")
                self.process_next()

    def process_next(self):
        if self.processing or not self.queue:
            return
        self.processing = True
        while self.queue:
            image_name = self.queue.pop(0)
            print(f"🚀 Processing: {image_name}")
            if send_image(image_name):
                wait_for_output_rename_and_upload(image_name)
        self.processing = False

# === Main Entry ===
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

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
