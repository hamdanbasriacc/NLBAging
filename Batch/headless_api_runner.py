import os
import sys
import json
import requests
import time

# Read image name from CLI arg
image_name = sys.argv[1] if len(sys.argv) > 1 else None
if not image_name:
    print("❌ No image provided to headless runner.")
    sys.exit(1)

COMFY_DIR = "C:/ComfyUI-CLI"
WORKFLOW_PATH = os.path.join(COMFY_DIR, "user", "default", "workflows", "aging_workflow.json")
API_URL = "http://127.0.0.1:8188/prompt"

with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ✅ Auto-wrap if needed
if "prompt" not in data and all(isinstance(v, dict) and "class_type" in v for v in data.values()):
    data = {"prompt": data}
elif "prompt" not in data:
    print("❌ Invalid workflow format: missing 'prompt'")
    sys.exit(1)

# ✅ Replace image in LoadImage node
found = False
for node in data["prompt"].values():
    if node.get("class_type") == "LoadImage":
        node["inputs"]["image"] = image_name
        found = True
        break

if not found:
    print("❌ Could not find LoadImage node in workflow.")
    sys.exit(1)

# 🔍 Debug
print(f"🧪 Updating workflow with image: {image_name}")

# 🚀 Submit to API
res = requests.post(API_URL, json={"prompt": data["prompt"]})
if res.status_code == 200:
    print("✅ Workflow submitted successfully.")
else:
    print("❌ Error submitting workflow:")
    print(res.status_code, res.text)
