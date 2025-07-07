import os
import time
import requests
import logging

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
PROCESSED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sent")
TARGET_URL_FILE = "/home/shared_comfy_data/latest_aged_url.txt"
CHECK_INTERVAL = 5  # seconds
STABILITY_WAIT = 2  # seconds between size checks

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
            files = {"image": (os.path.basename(image_path), img, "image/png")}
            response = requests.post(target_url, files=files)
        if response.status_code == 200:
            logging.info(f"✅ Uploaded: {os.path.basename(image_path)}")
            return True
        else:
            logging.warning(f"❌ Failed to upload {os.path.basename(image_path)}: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"❌ Exception uploading {os.path.basename(image_path)}: {e}")
    return False

def main():
    logging.info("👁️ watcher_send_output.py started")
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    while True:
        target_url = get_target_url()
        if not target_url:
            logging.info("⏳ No target URL found yet...")
            time.sleep(CHECK_INTERVAL)
            continue

        for filename in os.listdir(OUTPUT_DIR):
            if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            filepath = os.path.join(OUTPUT_DIR, filename)

            if not is_file_stable(filepath):
                logging.info(f"⏳ Waiting for file to stabilize: {filename}")
                continue

            if upload_image(filepath, target_url):
                os.remove(filepath)
                logging.info(f"🗑️ Deleted after upload: {filename}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
