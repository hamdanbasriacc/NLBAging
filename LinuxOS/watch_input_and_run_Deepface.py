#!/usr/bin/env python3

import os
import time
import json
import requests
import logging
import re
import getpass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from deepface import DeepFace
from PIL import Image
user = getpass.getuser()

# === Config===
if user == "admin":
    # PROD
    INPUT_DIR = "/home/admin/shared_comfy_data"
    OUTPUT_DIR = "/home/admin/ComfyUI/output"
    WORKFLOW_PATH = "/home/admin/ComfyUI/user/workflows/aging_upscaled.json"
else:
    # DEV
    INPUT_DIR = "/home/shared_comfy_data"
    OUTPUT_DIR = f"/home/{user}/ComfyUI/output"
    WORKFLOW_PATH = f"/home/{user}/ComfyUI/user/workflows/aging_upscaled.json"

print(f"🧭 Detected user: {user} — Running in {'PROD' if user == 'admin' else 'DEV'} mode")
print(f"📂 INPUT_DIR = {INPUT_DIR}")
print(f"📂 OUTPUT_DIR = {OUTPUT_DIR}")
print(f"📄 WORKFLOW_PATH = {WORKFLOW_PATH}")

# === ComfyUI Config DEV ===
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
            'asian': 'Southeast Asian',
            'indian': 'Indian Malaysian',
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

    # Determine scale_by value based on image resolution
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            if width < 480 and height < 640:
                scale_by_value = 2
            else:
                scale_by_value = 1
        print(f"🖼️ Image resolution: {width}x{height} → scale_by = {scale_by_value}")
    except Exception as e:
        logging.warning(f"⚠️ Could not read image size: {e}")
        scale_by_value = 1  # fallback to default

    if gender:
        print(f"🧠 Detected gender: {gender}")
    else:
        print("🧠 Gender not detected — no changes to gender in prompt")

    print(f"🧬 Detected ethnicity: {ethnicity}")

    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    for node in workflow.values():
        if isinstance(node, dict):
            # Update LoadImage path
            if node.get("class_type") == "LoadImage":
                if "inputs" in node and "image" in node["inputs"]:
                    node["inputs"]["image"] = image_path

            # Update prompt text with gender and ethnicity
            elif node.get("class_type") == "CLIPTextEncode":
                if "inputs" in node and "text" in node["inputs"]:
                    prompt_text = node["inputs"]["text"]
                    if isinstance(prompt_text, str):
                        if "{gender}" in prompt_text and gender:
                            prompt_text = prompt_text.replace("{gender}", gender)
                        if "{ethnicity}" in prompt_text and ethnicity:
                            prompt_text = prompt_text.replace("{ethnicity}", ethnicity)
                        node["inputs"]["text"] = prompt_text

            # Inject scale_by value based on resolution
            elif node.get("class_type") == "ImageScaleBy":
                if "inputs" in node and "scale_by" in node["inputs"]:
                    node["inputs"]["scale_by"] = scale_by_value

    return {"prompt": workflow}


def get_target_url_for_file(filename):
    # Extract the ticket ID using regex
    match = re.search(r'(ticket-[a-f0-9\-]+)', filename, re.IGNORECASE)
    if not match:
        logging.warning(f"⚠️ Could not extract ticket ID from filename: {filename}")
        return None

    ticket_id = match.group(1).lower()

    # Match any .url file that contains the ticket ID (not just prefix)
    for f in os.listdir(INPUT_DIR):
        if ticket_id in f.lower() and f.lower().endswith('.url'):
            url_path = os.path.join(INPUT_DIR, f)
            try:
                with open(url_path, "r") as f:
                    url = f.read().strip()
                    logging.info(f"🔗 Matched presigned URL from file: {url_path}")
                    return url
            except Exception as e:
                logging.warning(f"⚠️ Failed to read presigned URL file {url_path}: {e}")
                return None

    logging.warning(f"⚠️ No .url file found for ticket ID: {ticket_id}")
    return None



def is_file_stable(filepath):
    try:
        size1 = os.path.getsize(filepath)
        time.sleep(STABILITY_WAIT)
        size2 = os.path.getsize(filepath)
        return size1 == size2
    except Exception:
        return False

def upload_image(image_path, target_url, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            with open(image_path, "rb") as img:
                headers = {"Content-Type": "image/jpeg"}
                response = requests.put(target_url, data=img, headers=headers)
            if response.status_code in [200, 201]:
                logging.info(f"📤 Uploading to: {target_url}")
                logging.info(f"✅ Uploaded: {os.path.basename(image_path)} (attempt {attempt})")
                return True
            else:
                logging.info(f"📤 Uploading to: {target_url}")
                logging.warning(f"❌ Upload failed (attempt {attempt}): {response.status_code} - {response.text}")
        except Exception as e:
            logging.error(f"❌ Exception during upload (attempt {attempt}): {e}")
        time.sleep(2)
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

                # Try resolving just-in-time
                normalized_name = re.sub(r'^(Male|Female)_', '', input_filename, flags=re.IGNORECASE)
                target_url = get_target_url_for_file(normalized_name)
                if not target_url:
                    logging.warning(f"⚠️ No presigned URL available for {input_filename} (even after delay)")
                    return


                if upload_image(dst, target_url):
                    try:
                        # Remove output file
                        os.remove(dst)

                        # Remove original input image
                        input_path = os.path.join(INPUT_DIR, input_filename)
                        if os.path.exists(input_path):
                            os.remove(input_path)

                        # Match the actual URL file based on ticket ID (again)
                        match = re.search(r'(ticket-[a-f0-9\-]+)', input_filename, re.IGNORECASE)
                        if match:
                            ticket_id = match.group(1).lower()
                            for f in os.listdir(INPUT_DIR):
                                if ticket_id in f.lower() and f.lower().endswith(".url"):
                                    url_file_path = os.path.join(INPUT_DIR, f)
                                    try:
                                        os.remove(url_file_path)
                                        logging.info(f"🗑️ Removed URL file: {url_file_path}")
                                    except Exception as e:
                                        logging.warning(f"⚠️ Failed to delete URL file: {e}")

                        logging.info(f"🗑️ Cleaned up {input_filename} after successful upload")

                        # ✅ Mark this file as processed
                        handler.processed_files.add(input_filename)

                    except Exception as e:
                        logging.error(f"❌ Cleanup failed after successful upload: {e}")

                else:
                    logging.warning(f"❌ Upload failed after retries — keeping files for retry")

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
            # Strip gender prefix (if needed) to match the .url file
            normalized_name = re.sub(r'^(Male|Female)_', '', filename, flags=re.IGNORECASE)
            print(f"📸 Queued {filename} — will resolve URL later")

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
        for f in existing_images:
            # Simulate a filesystem event to properly queue and resolve URLs
            class DummyEvent:
                def __init__(self, path):
                    self.src_path = os.path.join(INPUT_DIR, path)
                    self.is_directory = False
            handler._maybe_queue_image(DummyEvent(f))


    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
