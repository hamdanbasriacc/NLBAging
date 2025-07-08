#!/usr/bin/env python3

import os
import time
import shutil
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SOURCE_DIR = "/home/shared_comfy_data"
DEST_DIR = "/home/hamdan_basri/ComfyUI/LinuxOS/input"
FLAG_PATH = "/home/hamdan_basri/ComfyUI/LinuxOS/upload_done.flag"
STABILITY_WAIT = 2  # seconds

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

os.makedirs(SOURCE_DIR, exist_ok=True)
os.makedirs(DEST_DIR, exist_ok=True)

def is_file_stable(filepath):
    try:
        size1 = os.path.getsize(filepath)
        time.sleep(STABILITY_WAIT)
        size2 = os.path.getsize(filepath)
        return size1 == size2
    except Exception:
        return False

class CopyHandler(FileSystemEventHandler):
    def __init__(self):
        self.seen = {}

    def on_created(self, event):
        self._handle(event)

    def on_modified(self, event):
        self._handle(event)

    def _handle(self, event):
        if event.is_directory:
            return

        src_path = event.src_path
        filename = os.path.basename(src_path)
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return

        now = time.time()
        last_seen = self.seen.get(filename, 0)
        if now - last_seen < 3:
            return  # Skip rapid duplicate events
        self.seen[filename] = now

        if not is_file_stable(src_path):
            logging.info(f"⏳ Waiting for file to stabilize: {filename}")
            return

        if os.path.exists(FLAG_PATH):
            logging.info(f"🛑 Upload in progress (flag exists), skipping: {filename}")
            return

        dest_path = os.path.join(DEST_DIR, filename)
        try:
            shutil.copy2(src_path, dest_path)
            logging.info(f"🚚 Moved {filename} to input folder.")
        except Exception as e:
            logging.warning(f"⚠️ Failed to move {filename}: {e}")

def main():
    logging.info(f"👁️ Watching folder: {SOURCE_DIR}")
    event_handler = CopyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=SOURCE_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
