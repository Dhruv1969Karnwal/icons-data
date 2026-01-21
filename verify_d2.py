import json
import sys
import os

# Import from test_mermaid.py
sys.path.append(os.getcwd())
from test_mermaid import IconResolver, D2Renderer

def verify_d2():
    print("🚀 Starting D2 Shape Verification...")
    
    resolver = IconResolver()
    renderer = D2Renderer()
    
    # Test Node - CloudHSM (should have shape: rectangle)
    # Test Node - S3 (should have shape: cylinder)
    
    nodes = [
        {
            "id": "hsm",
            "label": "Hardware Security",
            "technology": "CloudHSM",
            "layer": "security"
        },
        {
            "id": "storage",
            "label": "Data Store",
            "technology": "S3",
            "layer": "data"
        }
    ]
    
    print("\n🎨 Resolving icons...")
    resolved_nodes = resolver.resolve_icons(nodes)
    
    # Check if shape_type is attached
    for node in resolved_nodes:
        print(f"Node: {node['id']}, Tech: {node['technology']}, Icon: {node['icon_url']}, Shape: {node.get('shape_type')}")
    
    # Render to D2
    print("\n📝 Generating D2 Code...")
    json_ir = {
        "diagram_metadata": {"title": "Shape Test", "direction": "LR"},
        "nodes": resolved_nodes,
        "edges": []
    }
    
    d2_code = renderer.render(json_ir)
    print("--- D2 CODE START ---")
    print(d2_code)
    print("--- D2 CODE END ---")
    
    # Verification
    if "shape: rectangle" in d2_code or "shape: cylinder" in d2_code:
        print("\n✅ D2 Dynamic Shape logic is WORKING")
    else:
        print("\n❌ D2 Dynamic Shape logic is NOT WORKING (no specific shape found in code)")

if __name__ == "__main__":
    verify_d2()
