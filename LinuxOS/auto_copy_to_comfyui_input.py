
import os
import time
import shutil
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SOURCE_DIR = "/home/brandon_b_tan/Nlb_VideoStitching/pubsub/uploads"
DEST_DIR = "/home/hamdan_basri/ComfyUI/LinuxOS/input"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class ImageCopyHandler(FileSystemEventHandler):
    def __init__(self):
        self.processed = set()

    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        ext = os.path.splitext(filepath)[1].lower()
        if ext in VALID_EXTENSIONS:
            filename = os.path.basename(filepath)
            if filename in self.processed:
                return
            try:
                dest_path = os.path.join(DEST_DIR, filename)
                shutil.copy2(filepath, dest_path)
                logging.info(f"📥 Copied new image to input: {filename}")
                self.processed.add(filename)
            except Exception as e:
                logging.error(f"❌ Failed to copy {filename}: {e}")

if __name__ == "__main__":
    logging.info(f"👀 Watching for new images in: {SOURCE_DIR}")
    os.makedirs(DEST_DIR, exist_ok=True)
    event_handler = ImageCopyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=SOURCE_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
