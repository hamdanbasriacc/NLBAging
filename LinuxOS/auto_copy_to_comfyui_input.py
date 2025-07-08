import os
import time
import shutil
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SOURCE_DIR = "/home/shared_comfy_data"
DEST_DIR = "/home/hamdan_basri/ComfyUI/LinuxOS/input"
STABILITY_WAIT = 2  # seconds between size checks
SUPPORTED_EXT = (".png", ".jpg", ".jpeg")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def is_file_stable(filepath):
    try:
        size1 = os.path.getsize(filepath)
        time.sleep(STABILITY_WAIT)
        size2 = os.path.getsize(filepath)
        return size1 == size2
    except Exception:
        return False

class UploadWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        filename = os.path.basename(event.src_path)
        if not filename.lower().endswith(SUPPORTED_EXT):
            return

        source_path = os.path.join(SOURCE_DIR, filename)
        dest_path = os.path.join(DEST_DIR, filename)
        done_flag = os.path.join(DEST_DIR, filename + ".done")

        if os.path.exists(done_flag):
            logging.info(f"⏭️ Skipping {filename}, already processed.")
            return

        logging.info(f"📥 Detected new image: {filename}, checking stability...")
        if not is_file_stable(source_path):
            logging.warning(f"⚠️ Skipping unstable file: {filename}")
            return

        try:
            shutil.move(source_path, dest_path)
            logging.info(f"🚚 Moved {filename} to input folder.")
        except Exception as e:
            logging.error(f"❌ Failed to move {filename}: {e}")

if __name__ == "__main__":
    os.makedirs(SOURCE_DIR, exist_ok=True)
    os.makedirs(DEST_DIR, exist_ok=True)

    logging.info(f"👁️ Watching folder: {SOURCE_DIR}")
    event_handler = UploadWatcher()
    observer = Observer()
    observer.schedule(event_handler, SOURCE_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
