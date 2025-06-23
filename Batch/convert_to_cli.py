import json
from pathlib import Path

# Update these paths
INPUT_PATH = Path(r"C:\ComfyUI-CLI\user\default\workflows\aging_workflow.json")
OUTPUT_PATH = Path(r"C:\ComfyUI-CLI\user\default\workflows\aging_workflow_cleaned.json")

with INPUT_PATH.open("r", encoding="utf-8") as f:
    gui_data = json.load(f)

nodes = gui_data.get("nodes", [])
links = gui_data.get("links", [])
link_map = {link[0]: [str(link[1]), link[2]] for link in links}
cli_prompt = {}

for node in nodes:
    node_id = str(node["id"])
    inputs = {}
    input_defs = node.get("inputs", [])
    widget_vals = node.get("widgets_values", [])
    widget_idx = 0

    for i, input_def in enumerate(input_defs):
        name = input_def["name"]
        if input_def.get("link") is not None:
            link_id = input_def["link"]
            if link_id in link_map:
                inputs[name] = link_map[link_id]
        else:
            if widget_idx < len(widget_vals):
                val = widget_vals[widget_idx]
                inputs[name] = val if not (isinstance(val, list) and len(val) == 1) else val[0]
                widget_idx += 1

    cli_prompt[node_id] = {
        "class_type": node["type"],
        "inputs": inputs
    }

final_payload = {"prompt": cli_prompt}

with OUTPUT_PATH.open("w", encoding="utf-8") as f:
    json.dump(final_payload, f, indent=2)

print(f"✅ CLI-ready workflow saved to:\n{OUTPUT_PATH}")
