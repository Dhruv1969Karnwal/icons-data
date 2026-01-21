import json
from mermaid.utils.json_helper import robust_json_loads

def test_reproduction():
    print("🧪 Reproducing JSON parsing error...")
    
    # Mimic the user's failing response (shortened version of the 18k response)
    content = """1.  **Analyze the Request:**
 *   **Goal:** Extract architectural components and relationships from a natural language description into a specific JSON IR format.
 *   **Input:** A description of a React frontend and Postgres backend.

Thinking:
I need to generate a JSON object that follows the schema.
The user wants a simple web app.

{
  "version": "1.0",
  "diagram_metadata": {
    "type": "architecture",
    "direction": "LR",
    "title": "System Architecture",
    "auto_layout": true
  },
  "nodes": [
    {
      "id": "react_frontend",
      "label": "React Frontend",
      "technology": "react",
      "layer": "presentation",
      "description": "User interface"
    },
    {
      "id": "postgres_db",
      "label": "Postgres Database",
      "technology": "postgresql",
      "layer": "data",
      "description": "Primary data store"
    }
  ],
  "edges": [
    {
      "from": "react_frontend",
      "to": "postgres_db",
      "label": "queries",
      "type": "unidirectional"
    }
  ]
}

2. **Final verification:**
The JSON is valid and includes all components."""

    print(f"Content length: {len(content)}")
    print(f"Content starts with: {content[:50]}...")
    
    try:
        res = robust_json_loads(content)
        print("✅ Successfully parsed JSON!")
        print(f"Nodes: {len(res.get('nodes', []))}")
    except Exception as e:
        print(f"❌ Failed to parse: {e}")

if __name__ == "__main__":
    test_reproduction()
