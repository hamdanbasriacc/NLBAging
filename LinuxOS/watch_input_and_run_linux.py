#!/usr/bin/env python3

import os
import time
import json
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

INPUT_DIR = "/home/hamdan_basri/ComfyUI/LinuxOS/input"
OUTPUT_DIR = "/home/hamdan_basri/ComfyUI/LinuxOS/output"
WORKFLOW_PATH = "/home/hamdan_basri/ComfyUI/user/workflows/aging_workflow.json"
PROCESSED_DIR = os.path.join(INPUT_DIR, "processed")
COMFYUI_API_URL = "http://127.0.0.1:8188/prompt"

os.makedirs(PROCESSED_DIR, exist_ok=True)

def update_workflow(image_name):
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    for node in workflow.values():
        if isinstance(node, dict) and node.get("class_type") == "LoadImage":
            if "inputs" in node and "image" in node["inputs"]:
                node["inputs"]["image"] = image_name
    return {"prompt": workflow}

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
    while True:
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
                os.rename(os.path.join(INPUT_DIR, input_filename),
                          os.path.join(PROCESSED_DIR, input_filename))
                print(f"✅ Renamed output as {input_filename} and moved input to processed/")
                return
            except Exception as e:
                print(f"⚠️ Failed during rename/move: {e}")
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
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
