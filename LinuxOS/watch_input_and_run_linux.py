#!/usr/bin/env python3

import os
import time
import json
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

INPUT_DIR = "/home/hamdan_basri/ComfyUI/LinuxOS/input"
OUTPUT_DIR = "/home/hamdan_basri/ComfyUI/output"
WORKFLOW_PATH = "/home/hamdan_basri/ComfyUI/user/workflows/aging_workflow.json"
COMFYUI_API_URL = "http://127.0.0.1:8188/prompt"

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

def get_gender_from_filename(filename):
    name = filename.lower()
    if "female" in name:
        return "woman"
    elif "male" in name:
        return "man"
    return "person"

def update_workflow(image_name):
    image_path = os.path.join(INPUT_DIR, image_name)
    gender = get_gender_from_filename(image_name)

    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        workflow_json = json.load(f)

    # Convert from "nodes" array to prompt dict as required by ComfyUI
    prompt = {}
    for node in workflow_json.get("nodes", []):
        class_type = node.get("type")
        if not class_type:
            continue  # skip broken node

        inputs = {}
        for inp in node.get("inputs", []):
            if inp["name"] in ["image", "upload"]:
                if class_type == "LoadImage":
                    inputs[inp["name"]] = image_path
            elif "link" in inp and inp["link"] is not None:
                # This tells ComfyUI to connect this node input from another node
                for link in workflow_json["links"]:
                    if link[1] == node["id"] and link[3] == inp["name"]:
                        inputs[inp["name"]] = [str(link[0]), link[5]]
                        break

        # Update positive prompt with gender info
        if class_type == "CLIPTextEncode":
            # Detect positive prompt node (based on text content)
            widget_vals = node.get("widgets_values", [])
            if widget_vals and "natural aging" in widget_vals[0].lower():
                inputs["text"] = f"{gender}, {widget_vals[0]}"

        prompt[str(node["id"])] = {
            "class_type": class_type,
            "inputs": inputs
        }

    return {"prompt": prompt}


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

def wait_for_output_and_rename(input_filename):
    print(f"🔍 Waiting for output for: {input_filename}")
    prev_files = set(os.listdir(OUTPUT_DIR))
    for _ in range(120):
        time.sleep(1)
        current_files = set(os.listdir(OUTPUT_DIR))
        new_files = current_files - prev_files
        candidates = [f for f in new_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if candidates:
            output_file = candidates[0]
            src = os.path.join(OUTPUT_DIR, output_file)
            dst = os.path.join(OUTPUT_DIR, input_filename)
            try:
                with open(src, "rb") as fsrc:
                    content = fsrc.read()
                with open(dst, "wb") as fdst:
                    fdst.write(content)
                os.remove(src)
                os.remove(os.path.join(INPUT_DIR, input_filename))
                print(f"✅ Renamed output as {input_filename} and deleted input image.")
                return
            except Exception as e:
                print(f"⚠️ Failed during rename/delete: {e}")
                return

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
                wait_for_output_and_rename(image_name)
        self.processing = False

if __name__ == "__main__":
    print(f"👀 Watching input: {INPUT_DIR}")
    print(f"👀 Watching output: {OUTPUT_DIR}")
    observer = Observer()
    handler = InputImageHandler()
    observer.schedule(handler, INPUT_DIR, recursive=False)
    observer.start()

    wait_for_comfyui_server()

    # Process any images already in input
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
