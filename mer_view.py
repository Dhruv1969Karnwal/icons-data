import json
import subprocess
from pathlib import Path

# Load your output JSON
with open("output_modular.json", "r") as f:
    result = json.load(f)

output_dir = Path("./test_outputs")
output_dir.mkdir(exist_ok=True)

print("🎨 Testing all diagram formats...\n")

# 1. Mermaid
print("✅ 1. MERMAID")
with open(output_dir / "architecture.md", "w") as f:
    f.write("```mermaid\n")
    f.write(result["mermaid"])
    f.write("\n```")
print(f"   Saved: {output_dir / 'architecture.md'}")

# 2. Draw.io XML
print("✅ 2. DRAW.IO")
with open(output_dir / "architecture.drawio", "w") as f:
    f.write(result["drawio_xml"])
print(f"   Saved: {output_dir / 'architecture.drawio'}")
print(f"   Open in: https://app.diagrams.net → File → Open")

# 3. D2
print("✅ 3. D2")
with open(output_dir / "architecture.d2", "w") as f:
    f.write(result["d2_code"])
print(f"   Saved: {output_dir / 'architecture.d2'}")
try:
    subprocess.run(["d2", str(output_dir / "architecture.d2"), str(output_dir / "architecture.png")])
    print(f"   PNG: {output_dir / 'architecture.png'}")
except:
    print("   ⚠️  D2 not installed. Run: brew install d2")

# 4. Diagrams.py
print("✅ 4. DIAGRAMS.PY")
with open(output_dir / "generate_diagram.py", "w") as f:
    f.write(result["diagrams_py"])
print(f"   Saved: {output_dir / 'generate_diagram.py'}")
try:
    subprocess.run(["python", str(output_dir / "generate_diagram.py")])
    print(f"   PNG: {output_dir / 'architecture.png'}")
except:
    print("   ⚠️  Diagrams.py not installed. Run: pip install diagrams")

# 5. D3.js JSON
print("✅ 5. D3.JS")
with open(output_dir / "d3_data.json", "w") as f:
    json.dump(result["d3_json"], f, indent=2)
print(f"   JSON: {output_dir / 'd3_data.json'}")

print("\n🎉 All formats exported successfully!")
print(f"📁 Check {output_dir}/ directory for files")