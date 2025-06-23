import os
import time
import requests

# Configuration
output_dir = r"C:\ComfyUI-CLI\output"  # Make sure this folder exists
webhook_url = "	https://webhook.site/29c50f50-1817-4af8-890f-76b7fc421ee2"  # Replace with your webhook URL
poll_interval = 5  # seconds

# Track seen files
seen_files = set(os.listdir(output_dir))

def send_to_webhook(file_path):
    with open(file_path, "rb") as f:
        files = {'file': (os.path.basename(file_path), f)}
        response = requests.post(webhook_url, files=files)
        return response.status_code

# Monitoring loop
print(f"👀 Watching folder: {output_dir}")
try:
    while True:
        current_files = set(os.listdir(output_dir))
        new_files = current_files - seen_files
        for file in new_files:
            file_path = os.path.join(output_dir, file)
            if os.path.isfile(file_path):
                print(f"📤 Sending {file} to webhook...")
                status = send_to_webhook(file_path)
                print(f"✅ Sent {file} - HTTP {status}")
        seen_files = current_files
        time.sleep(poll_interval)
except KeyboardInterrupt:
    print("🛑 Stopped monitoring.")
except Exception as e:
    print(f"❌ Error: {e}")
