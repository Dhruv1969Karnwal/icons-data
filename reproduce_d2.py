import sys
import os
import json

# Add current directory to path to import mermaid
sys.path.append(os.getcwd())

from mermaid.renderers.mermaid_renderer import MermaidRenderer

json_ir_path = "output_modular.json"
if os.path.exists(json_ir_path):
    with open(json_ir_path, 'r') as f:
        data = json.load(f)
        # The file has "json_ir" as a top level key
        json_ir = data.get("json_ir", data)
else:
    # Use the example from d2.py
    from mermaid.renderers.d2 import json_ir

renderer = MermaidRenderer()
d2_code = renderer.render(json_ir)

print(d2_code)

output_path = "reproduce_output.mmd"
with open(output_path, "w") as f:
    f.write(d2_code)
print(f"\nOutput written to {output_path}")
