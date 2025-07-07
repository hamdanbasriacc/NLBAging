import os
import time
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# CONFIG
source_dir = "/home/shared_comfy_data"
dest_dir = "/home/hamdan_basri/ComfyUI/LinuxOS/input"
valid_extensions = (".png", ".jpg", ".jpeg", ".webp")
processed_files = set()
check_interval = 1  # seconds

class MoveNewImagesHandler(FileSystemEventHandler):
    def on_created(self, event):
        self.process(event)

    def on_modified(self, event):
        self.process(event)

    def process(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        if filepath.lower().endswith(valid_extensions):
            filename = os.path.basename(filepath)
            if filename in processed_files:
                return
            dest_path = os.path.join(dest_dir, filename)
            try:
                shutil.move(filepath, dest_path)
                print(f"🚚 Moved {filename} to input folder")
                processed_files.add(filename)
            except Exception as e:
                print(f"❌ Failed to move {filename}: {e}")

if __name__ == "__main__":
    print(f"👁️ Watching folder: {source_dir}")
    os.makedirs(dest_dir, exist_ok=True)

    event_handler = MoveNewImagesHandler()
    observer = Observer()
    observer.schedule(event_handler, path=source_dir, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(check_interval)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
