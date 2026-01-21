import json
from typing import Dict
from litellm import completion
from mermaid.utils.json_helper import robust_json_loads

class PlannerAgent:
    """Extracts architectural components and relationships from user input."""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def extract_architecture(self, user_input: str) -> Dict:
        """Use LLM to extract architecture from natural language."""
        
        print(f"\n🤖 [PlannerAgent] Starting architecture extraction")
        print(f"   📝 User input length: {len(user_input)} characters")
        
        system_prompt = """You are an expert system architect. Your task is to extract architectural components and their relationships from natural language descriptions.

Generate a JSON IR (Intermediate Representation) with this exact structure:
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
      "id": "unique_id",
      "label": "Component Name",
      "technology": "technology_name",
      "layer": "presentation|application|data|infrastructure",
      "description": "brief description"
    }
  ],
  "edges": [
    {
      "from": "node_id",
      "to": "node_id",
      "label": "connection type",
      "type": "unidirectional|bidirectional"
    }
  ]
}

Rules:
1. Use descriptive unique IDs (e.g., "react_frontend", "postgres_db")
2. Identify the actual technology (e.g., "react", "postgresql", "aws-s3")
3. Classify each component into a layer
4. Create edges showing data/control flow
5. Return ONLY valid JSON. 
6. DO NOT include any markdown formatting (no ```json).
7. DO NOT include any preamble, thinking process, or post-explanation.
8. Start your response with { and end it with }.

CRITICAL: If you fail to return ONLY valid JSON, the system will crash. Be extremely precise."""

        user_prompt = f"User Input: {user_input}\n\nGenerate the JSON IR:"

        print(f"   📤 [PlannerAgent] Sending request to LLM...")
        print(f"   ⚙️  Model: {self.config['model']}")
        print(f"   🌐 Base URL: {self.config['base_url']}")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = completion(
                model=self.config["model"],
                api_base=self.config["base_url"],
                api_key=self.config["api_key"],
                messages=messages,
                temperature=0.3,
                # request_timeout=30  # Add 30s timeout to prevent hanging
            )
            
            print(f"   ✅ [PlannerAgent] Received response from LLM")
            
            # Check if response is valid
            if not response or not hasattr(response, 'choices') or not response.choices:
                print(f"   ❌ [PlannerAgent] Invalid response structure from LLM")
                print(f"   📦 Response object: {response}")
                return self._create_empty_ir()
            
            # Check if message content exists
            if not response.choices[0].message or not hasattr(response.choices[0].message, 'content'):
                print(f"   ❌ [PlannerAgent] No message content in response")
                print(f"   📦 Response choices: {response.choices}")
                return self._create_empty_ir()
            
            content = response.choices[0].message.content
            
            # Check if content is None
            if content is None:
                print(f"   ❌ [PlannerAgent] Content is None")
                print(f"   📦 Full response: {response}")
                print(f"   📦 Message: {response.choices[0].message}")
                return self._create_empty_ir()
            
            print(f"   📊 Response length: {len(content)} characters")
            print(f"   📄 Raw response (first 200 chars): {content[:200]}...")
            
            print(f"   🔍 [PlannerAgent] Parsing JSON...")
            json_ir = robust_json_loads(content)
            print(f"   ✅ [PlannerAgent] Successfully parsed JSON IR")
            print(f"   📊 Extracted {len(json_ir.get('nodes', []))} nodes and {len(json_ir.get('edges', []))} edges")
            
            # Print node details
            for idx, node in enumerate(json_ir.get('nodes', []), 1):
                print(f"      Node {idx}: {node.get('id')} - {node.get('label')} ({node.get('technology')})")
            
            return json_ir
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"   ❌ [PlannerAgent] JSON parsing error: {e}")
            # If we haven't already printed the content, print it now for debugging
            if 'content' in locals() and len(content) < 1000:
                print(f"   📄 Content that failed to parse:\n{content}")
            print(f"   🔄 Returning empty IR structure")
            return self._create_empty_ir()
        except Exception as e:
            print(f"   ❌ [PlannerAgent] Unexpected error: {type(e).__name__}: {e}")
            import traceback
            print(f"   📍 Traceback:\n{traceback.format_exc()}")
            return self._create_empty_ir()
    
    def _create_empty_ir(self) -> Dict:
        """Return empty but valid IR structure."""
        print(f"   ⚠️  [PlannerAgent] Creating empty IR structure as fallback")
        return {
            "version": "1.0",
            "diagram_metadata": {
                "type": "architecture",
                "direction": "LR",
                "title": "System Architecture",
                "auto_layout": True
            },
            "nodes": [],
            "edges": []
        }
