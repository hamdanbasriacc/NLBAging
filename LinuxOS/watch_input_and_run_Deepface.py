#!/usr/bin/env python3

import os
import time
import json
import requests
import logging
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from deepface import DeepFace

# === Config ===
INPUT_DIR = "/home/admin/shared_comfy_data"
OUTPUT_DIR = "/home/admin/ComfyUI/output"
TARGET_URL_FILE = "/home/admin/shared_comfy_data/latest_aged_url.txt"
WORKFLOW_PATH = "/home/admin/ComfyUI/user/workflows/aging_workflow.json"
COMFYUI_API_URL = "http://127.0.0.1:8188/prompt"
STABILITY_WAIT = 2  # seconds

# === Logging Setup ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Ensure Directories Exist ===
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

def detect_ethnicity_from_image(image_path):
    try:
        analysis = DeepFace.analyze(img_path=image_path, actions=['race'], enforce_detection=False)
        dominant = analysis[0]['dominant_race'].lower()

        # Map DeepFace's result to more region-specific descriptors
        ethnicity_map = {
            'asian': 'Chinese Singaporean',
            'indian': 'Indian Singaporean',
            'white': 'Malay',
            'latino hispanic': 'brown-skinned Malay',
            'black': 'dark-skinned Malay',
            'middle eastern': 'brown-skinned Malay'
        }

        return ethnicity_map.get(dominant, 'Southeast Asian')
    except Exception as e:
        logging.warning(f"⚠️ DeepFace failed to analyze image: {e}")
        return 'Southeast Asian'


def detect_gender_from_filename(filename):
    lower = filename.lower()
    if "female" in lower or "woman" in lower:
        return "woman"
    elif "male" in lower or "man" in lower:
        return "man"
    return None

def update_workflow(image_name):
    image_path = os.path.join(INPUT_DIR, image_name)
    gender = detect_gender_from_filename(image_name)
    ethnicity = detect_ethnicity_from_image(image_path)

    if gender:
        print(f"🧠 Detected gender: {gender}")
    else:
        print("🧠 Gender not detected — no changes to gender in prompt")

    print(f"🧬 Detected ethnicity: {ethnicity}")

    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    for node in workflow.values():
        if isinstance(node, dict) and node.get("class_type") == "LoadImage":
            if "inputs" in node and "image" in node["inputs"]:
                node["inputs"]["image"] = image_path
        elif node.get("class_type") == "CLIPTextEncode":
            if "inputs" in node and "text" in node["inputs"]:
                prompt_text = node["inputs"]["text"]
                if isinstance(prompt_text, str):
                    if "{gender}" in prompt_text and gender:
                        prompt_text = prompt_text.replace("{gender}", gender)
                    if "{ethnicity}" in prompt_text and ethnicity:
                        prompt_text = prompt_text.replace("{ethnicity}", ethnicity)
                    node["inputs"]["text"] = prompt_text

    return {"prompt": workflow}


def get_target_url():
    try:
        with open(TARGET_URL_FILE, "r") as f:
            url = f.read().strip()
            if url:
                return url
    except Exception as e:
        logging.warning(f"⚠️ Failed to read target URL: {e}")
    return None

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

    # Clean the filename by removing 'Male' or 'Female' with surrounding underscores (or at edges)
    cleaned_name = re.sub(r'(^|_)Male(_|$)', r'\1', input_filename, flags=re.IGNORECASE)
    cleaned_name = re.sub(r'(^|_)Female(_|$)', r'\1', cleaned_name, flags=re.IGNORECASE)
    cleaned_name = re.sub(r'__+', '_', cleaned_name)  # collapse double underscores
    cleaned_name = cleaned_name.strip('_')  # remove leading/trailing underscores

    for _ in range(300):  # 5 minutes max
        time.sleep(1)
        current_files = set(os.listdir(OUTPUT_DIR))
        new_files = current_files - prev_files
        candidates = [f for f in new_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if candidates:
            output_file = candidates[0]
            src = os.path.join(OUTPUT_DIR, output_file)
            dst = os.path.join(OUTPUT_DIR, cleaned_name)

            try:
                # Copy content from temp name to final renamed file
                with open(src, "rb") as fsrc:
                    content = fsrc.read()
                with open(dst, "wb") as fdst:
                    fdst.write(content)
                os.remove(src)
                print(f"📄 Renamed output to: {cleaned_name}")

                # Upload after successful rename
                target_url = handler.image_to_url.get(input_filename)
                if not target_url:
                    logging.warning(f"⚠️ No presigned URL stored for {input_filename}")
                    return

                if upload_image(dst, target_url):
                    os.remove(dst)
                    os.remove(os.path.join(INPUT_DIR, input_filename))
                    logging.info(f"🗑️ Cleaned up {input_filename} after successful upload")

                    # ✅ Mark this file as processed (important: only after successful upload & cleanup)
                    handler.processed_files.add(input_filename)

                else:
                    logging.warning(f"❌ Upload failed — keeping files for retry")
                return

            except Exception as e:
                print(f"⚠️ Failed during output handling: {e}")
                return


class InputImageHandler(FileSystemEventHandler):
    def __init__(self):
        self.queue = []
        self.processing = False
        self.image_to_url = {}
        self.processed_files = set()
        self.file_mtimes = {}
        

    def _maybe_queue_image(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return

        filepath = os.path.join(INPUT_DIR, filename)
        try:
            current_mtime = os.path.getmtime(filepath)
        except FileNotFoundError:
            return  # file was deleted too quickly

        prev_mtime = self.file_mtimes.get(filename)

        # Only requeue if:
        # - it's new
        # - OR it has a changed mtime (meaning it's newly copied in again)
        if filename not in self.processed_files or current_mtime != prev_mtime:
            self.file_mtimes[filename] = current_mtime
            self.queue.append(filename)
            url = get_target_url()
            if url:
                self.image_to_url[filename] = url
                print(f"📸 Queued {filename} with updated mtime")
            else:
                logging.warning(f"⚠️ No presigned URL for {filename}")
            if not self.processing:
                self.process_next()

    def on_created(self, event):
        self._maybe_queue_image(event)

    def on_modified(self, event):
        self._maybe_queue_image(event)

    def process_next(self):
        if self.processing or not self.queue:
            return
        self.processing = True

        while self.queue:
            image_name = self.queue.pop(0)
            print(f"🚀 Processing: {image_name}")

            # Wait for input file to stabilize
            input_path = os.path.join(INPUT_DIR, image_name)
            for _ in range(5):
                try:
                    size1 = os.path.getsize(input_path)
                    time.sleep(1)
                    size2 = os.path.getsize(input_path)
                    if size1 == size2:
                        break
                except FileNotFoundError:
                    time.sleep(1)
            else:
                print(f"Waiting for next image...")
                # logging.warning(f"⚠️ Waiting for next image...")
                continue  # move to next image

            # Now it's safe to submit
            if send_image(image_name):
               wait_for_output_rename_and_upload(image_name)

        self.processing = False


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
