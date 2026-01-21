import json
import requests
from typing import Dict, List, Optional, Tuple
from litellm import completion
import time
from functools import lru_cache
import os
from pathlib import Path

# Configuration
LITELLM_CONFIG = {
    "base_url": "https://backend.v3.codemateai.dev/v2",
    "api_key": "ba0981d9-4fb5-4974-9dae-0c878330c22a",
    "model": "openai/web_chat"
}

ICONIFY_API_BASE = "https://api.iconify.design"
QDRANT_API_BASE = "http://localhost:8001/api/rag"
DEFAULT_ICON = "https://api.iconify.design/carbon:cube.svg"

import random

class IconResolver:
    """Resolves technology names to Iconify icon URLs with caching."""
    
    def __init__(self):
        self.cache = {}
        self.static_icons = []
        self._load_static_index()

    def _load_static_index(self):
        """Load static icon index from JSON file."""
        paths_to_try = [
            "icons_rag.json",
            "output/icons_rag.json",
            "c:/Users/Dhruv/Desktop/CodeMate.AI/extra_research/terrastruct-icons/icons_rag.json"
        ]
        for path in paths_to_try:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.static_icons = json.load(f)
                    print(f"   📂 [IconResolver] Loaded {len(self.static_icons)} icons from {path}")
                    return
                except Exception as e:
                    print(f"   ⚠️ [IconResolver] Failed to load {path}: {e}")
        print("   ❌ [IconResolver] Could not find any static icon index file.")

    @lru_cache(maxsize=500)
    def search_icon(self, technology: str) -> Tuple[Optional[str], Optional[str]]:
        """Search for an icon using local static index (primary), then fallback to random static icon."""
        print(f"\n🔍 [IconResolver] Searching icon for technology: '{technology}'")
        
        # 0. Try local static index first
        if self.static_icons:
            print(f"   📡 [IconResolver] Trying local static lookup for '{technology}'...")
            tech_lower = technology.lower()
            for icon in self.static_icons:
                # Match by slug, display_name or title
                if tech_lower in icon.get("slug", "").lower() or \
                   tech_lower in icon.get("display_name", "").lower() or \
                   tech_lower in icon.get("id", "").lower():
                    icon_url = icon.get("url")
                    shape_type = icon.get("shape_type", "image")
                    print(f"   ✅ [IconResolver] Found icon in static index: {icon_url} (Shape: {shape_type})")
                    return icon_url, shape_type
            
            # If no direct match found in static list, use a random one as requested
            print(f"   ⚠️ [IconResolver] No match for '{technology}' in static index. Using random fallback.")
            random_icon = random.choice(self.static_icons)
            icon_url = random_icon.get("url")
            shape_type = random_icon.get("shape_type", "image")
            print(f"   🎲 [IconResolver] Randomly selected: {icon_url} (Shape: {shape_type})")
            return icon_url, shape_type

        # 1. Fallback to Qdrant search (only if static icons weren't loaded)
        try:
            print(f"   📡 [IconResolver] Trying Qdrant search for '{technology}'...")
            qdrant_url = f"{QDRANT_API_BASE}/search"
            params = {"q": technology, "top_k": 1}
            response = requests.get(qdrant_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    hit = results[0]
                    icon_url = hit.get("url")
                    shape_type = hit.get("shape_type")
                    if icon_url:
                        print(f"   ✅ [IconResolver] Found icon via Qdrant: {icon_url} (Shape: {shape_type})")
                        return icon_url, shape_type
            else:
                print(f"   ❌ [IconResolver] Qdrant search failed with status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ [IconResolver] Qdrant search exception: {type(e).__name__}: {e}")

        print(f"   ❌ [IconResolver] Using absolute default icon for '{technology}'")
        return DEFAULT_ICON, "image"
    
    def resolve_icons(self, nodes: List[Dict]) -> List[Dict]:
        """Resolve icon URLs for all nodes."""
        print(f"\n🎨 [IconResolver] Starting icon resolution for {len(nodes)} nodes")
        for idx, node in enumerate(nodes, 1):
            node_id = node.get("id", f"node_{idx}")
            print(f"\n   🔹 [IconResolver] Processing node {idx}/{len(nodes)}: '{node_id}'")
            if "technology" in node and not node.get("icon_url"):
                tech = node["technology"]
                print(f"      Technology: '{tech}'")
                icon_url, shape_type = self.search_icon(tech)
                node["icon_url"] = icon_url
                node["shape_type"] = shape_type
                print(f"      ✅ Resolved to: {icon_url} (Shape: {shape_type})")
            elif node.get("icon_url"):
                print(f"      ℹ️  Icon URL already exists: {node['icon_url']}")
            else:
                print(f"      ⚠️  No 'technology' field found, skipping icon resolution")
        print(f"\n✅ [IconResolver] Icon resolution complete!\n")
        return nodes


class PlannerAgent:
    """Extracts architectural components and relationships from user input."""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def extract_architecture(self, user_input: str) -> Dict:
        """Use LLM to extract architecture from natural language."""
        
        print(f"\n🤖 [PlannerAgent] Starting architecture extraction")
        print(f"   📝 User input length: {len(user_input)} characters")
        
        prompt = f"""You are an expert system architect. Extract the architectural components and their relationships from the user's description.

User Input: {user_input}

Generate a JSON IR (Intermediate Representation) with this exact structure:
{{
  "version": "1.0",
  "diagram_metadata": {{
    "type": "architecture",
    "direction": "LR",
    "title": "System Architecture",
    "auto_layout": true
  }},
  "nodes": [
    {{
      "id": "unique_id",
      "label": "Component Name",
      "technology": "technology_name",
      "layer": "presentation|application|data|infrastructure",
      "description": "brief description"
    }}
  ],
  "edges": [
    {{
      "from": "node_id",
      "to": "node_id",
      "label": "connection type",
      "type": "unidirectional|bidirectional"
    }}
  ]
}}

Rules:
1. Use descriptive unique IDs (e.g., "react_frontend", "postgres_db")
2. Identify the actual technology (e.g., "react", "postgresql", "aws-s3")
3. Classify each component into a layer
4. Create edges showing data/control flow
5. Return ONLY valid JSON, no markdown or explanations

CRITICAL: Your response must contain ONLY the JSON object, nothing else. No explanations, no thinking process, no preamble. Start directly with {{ and end with }}.

Generate the JSON IR:"""

        print(f"   📤 [PlannerAgent] Sending request to LLM...")
        print(f"   ⚙️  Model: {self.config['model']}")
        print(f"   🌐 Base URL: {self.config['base_url']}")
        
        try:
            response = completion(
                model=self.config["model"],
                api_base=self.config["base_url"],
                api_key=self.config["api_key"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
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
            
            # Extract JSON from markdown code blocks if present
            original_content = content
            if "```json" in content:
                print(f"   🔧 [PlannerAgent] Detected JSON markdown block, extracting...")
                content = content.split("```json")[1].split("```")[0].strip()
                print(f"   ✓ Extracted JSON length: {len(content)} characters")
            elif "```" in content:
                print(f"   🔧 [PlannerAgent] Detected generic markdown block, extracting...")
                content = content.split("```")[1].split("```")[0].strip()
                print(f"   ✓ Extracted content length: {len(content)} characters")
            
            # Additional fallback: try to find JSON object boundaries
            if not content.strip().startswith("{"):
                print(f"   ⚠️  [PlannerAgent] Content doesn't start with {{, searching for JSON object...")
                # Find the first { and last }
                start_idx = content.find("{")
                end_idx = content.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    content = content[start_idx:end_idx+1]
                    print(f"   ✓ Extracted JSON object from position {start_idx} to {end_idx}")
                    print(f"   ✓ Cleaned content length: {len(content)} characters")
                else:
                    print(f"   ❌ [PlannerAgent] Could not find JSON object boundaries")
                    print(f"   📄 Full content:\n{content}")
                    return self._create_empty_ir()
            
            print(f"   🔍 [PlannerAgent] Parsing JSON...")
            json_ir = json.loads(content)
            print(f"   ✅ [PlannerAgent] Successfully parsed JSON IR")
            print(f"   📊 Extracted {len(json_ir.get('nodes', []))} nodes and {len(json_ir.get('edges', []))} edges")
            
            # Print node details
            for idx, node in enumerate(json_ir.get('nodes', []), 1):
                print(f"      Node {idx}: {node.get('id')} - {node.get('label')} ({node.get('technology')})")
            
            return json_ir
            
        except json.JSONDecodeError as e:
            print(f"   ❌ [PlannerAgent] JSON parsing error: {e}")
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


class AuditorAgent:
    """Reviews and validates the architectural design."""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def audit(self, json_ir: Dict) -> Tuple[bool, List[str], Optional[Dict]]:
        """
        Audit the JSON IR for best practices and logical consistency.
        Returns: (is_valid, suggestions, corrected_ir)
        """
        
        print(f"\n🔍 [AuditorAgent] Starting architecture audit")
        print(f"   📊 Auditing {len(json_ir.get('nodes', []))} nodes and {len(json_ir.get('edges', []))} edges")
        
        prompt = f"""You are a senior solutions architect reviewing a system design.

Current Design (JSON IR):
{json.dumps(json_ir, indent=2)}

Review this architecture for:
1. Missing critical components (load balancers, caching, monitoring)
2. Security concerns (exposed databases, missing authentication)
3. Scalability issues (single points of failure)
4. Best practices violations
5. Logical inconsistencies in connections

Provide your response in this JSON format:
{{
  "is_valid": true/false,
  "suggestions": ["suggestion 1", "suggestion 2"],
  "severity": "low|medium|high",
  "corrected_ir": {{ ... }} // only if is_valid is false
}}

If the design is fundamentally sound, set is_valid to true and provide minor suggestions.
If there are critical issues, set is_valid to false and provide a corrected_ir.

CRITICAL REQUIREMENTS FOR corrected_ir:
1. Must include "technology" field for every node (e.g., "nodejs", "postgresql", "redis")
2. Every edge must have "from", "to", "label", and "type" fields
3. Edge format: {{"from": "node_id", "to": "node_id", "label": "connection", "type": "unidirectional"}}
4. Your response must contain ONLY the JSON object, nothing else. No explanations before or after.

Response:"""

        print(f"   📤 [AuditorAgent] Sending audit request to LLM...")
        print(f"   ⚙️  Model: {self.config['model']}")
        
        try:
            response = completion(
                model=self.config["model"],
                api_base=self.config["base_url"],
                api_key=self.config["api_key"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            print(f"   ✅ [AuditorAgent] Received audit response from LLM")
            
            # Check if response is valid
            if not response or not hasattr(response, 'choices') or not response.choices:
                print(f"   ❌ [AuditorAgent] Invalid response structure from LLM")
                print(f"   📦 Response object: {response}")
                return True, ["Audit failed - invalid response structure"], None
            
            # Check if message content exists
            if not response.choices[0].message or not hasattr(response.choices[0].message, 'content'):
                print(f"   ❌ [AuditorAgent] No message content in response")
                return True, ["Audit failed - no message content"], None
            
            content = response.choices[0].message.content
            
            # Check if content is None
            if content is None:
                print(f"   ❌ [AuditorAgent] Content is None")
                print(f"   📦 Full response: {response}")
                return True, ["Audit failed - content is None"], None
            
            print(f"   📊 Audit response length: {len(content)} characters")
            print(f"   📄 Raw audit response (first 200 chars): {content[:200]}...")
            
            # Extract JSON
            if "```json" in content:
                print(f"   🔧 [AuditorAgent] Extracting JSON from markdown block...")
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                print(f"   🔧 [AuditorAgent] Extracting from generic markdown block...")
                content = content.split("```")[1].split("```")[0].strip()
            
            # Additional fallback: try to find JSON object boundaries
            if not content.strip().startswith("{"):
                print(f"   ⚠️  [AuditorAgent] Content doesn't start with {{, searching for JSON object...")
                start_idx = content.find("{")
                end_idx = content.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    content = content[start_idx:end_idx+1]
                    print(f"   ✓ Extracted JSON object from position {start_idx} to {end_idx}")
                else:
                    print(f"   ❌ [AuditorAgent] Could not find JSON object boundaries")
                    return True, ["Audit failed - invalid JSON format"], None
            
            print(f"   🔍 [AuditorAgent] Parsing audit result JSON...")
            audit_result = json.loads(content)
            
            is_valid = audit_result.get("is_valid", True)
            suggestions = audit_result.get("suggestions", [])
            severity = audit_result.get("severity", "unknown")
            corrected_ir = audit_result.get("corrected_ir")
            
            print(f"   📋 [AuditorAgent] Audit Results:")
            print(f"      ✓ Is Valid: {is_valid}")
            print(f"      ✓ Severity: {severity}")
            print(f"      ✓ Number of suggestions: {len(suggestions)}")
            print(f"      ✓ Has corrected IR: {corrected_ir is not None}")
            
            if suggestions:
                print(f"   💡 Suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"      {i}. {suggestion}")
            
            if corrected_ir:
                print(f"   🔄 [AuditorAgent] Corrected IR provided with {len(corrected_ir.get('nodes', []))} nodes")
            
            return (is_valid, suggestions, corrected_ir)
            
        except json.JSONDecodeError as e:
            print(f"   ❌ [AuditorAgent] JSON parsing error in audit result: {e}")
            print(f"   📄 Content that failed to parse:\n{content}")
            print(f"   🔄 Proceeding with original design")
            return True, ["Audit failed, proceeding with original design"], None
        except Exception as e:
            print(f"   ❌ [AuditorAgent] Unexpected error during audit: {type(e).__name__}: {e}")
            import traceback
            print(f"   📍 Traceback:\n{traceback.format_exc()}")
            return True, ["Audit failed, proceeding with original design"], None
class DiagramsPyRenderer:
    """Renders JSON IR to Diagrams.py Python code using only Custom nodes."""
    
    def __init__(self, output_format: str = "png", output_dir: str = "./diagrams"):
        """
        Initialize Diagrams.py renderer.
        
        Args:
            output_format: Output format (png, jpg, svg, pdf)
            output_dir: Directory to save generated diagrams
        """
        self.output_format = output_format
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_cluster_name(self, layer: str) -> str:
        """Get cluster name based on architectural layer."""
        layer_names = {
            "presentation": "Presentation Layer",
            "application": "Application Layer",
            "data": "Data Layer",
            "infrastructure": "Infrastructure Layer"
        }
        return layer_names.get(layer, "Components")
    
    def render(self, json_ir: Dict, filename: str = "architecture") -> str:
        """
        Convert JSON IR to Diagrams.py Python code using only Custom nodes.
        
        Returns:
            Python code as string that can be executed to generate diagram
        """
        print(f"\n🎨 [DiagramsPyRenderer] Starting Diagrams.py code generation")
        
        metadata = json_ir.get("diagram_metadata", {})
        nodes = json_ir.get("nodes", [])
        edges = json_ir.get("edges", [])
        
        title = metadata.get("title", "Architecture Diagram")
        direction = metadata.get("direction", "LR")
        
        print(f"   📊 Metadata:")
        print(f"      Title: {title}")
        print(f"      Direction: {direction}")
        print(f"   📦 Content: {len(nodes)} nodes, {len(edges)} edges")
        
        # Group nodes by layer
        layers = {}
        for node in nodes:
            layer = node.get("layer", "application")
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(node)
        
        print(f"   📦 [DiagramsPyRenderer] Grouped nodes into layers")
        
        # Generate imports (minimal - only need Custom)
        imports = set()
        imports.add("from diagrams import Diagram, Cluster, Edge")
        imports.add("from diagrams.custom import Custom")
        
        print(f"   📦 [DiagramsPyRenderer] Generated {len(imports)} import statements")
        
        # Generate Python code
        code_lines = []
        
        # Add imports
        code_lines.extend(sorted(imports))
        code_lines.append("")
        
        # Start diagram
        graph_attr = {
            "fontsize": "16",
            "bgcolor": "white",
            "pad": "0.5"
        }
        
        if direction == "LR":
            graph_attr["rankdir"] = "LR"
        elif direction == "TB":
            graph_attr["rankdir"] = "TB"
        
        code_lines.append(f'with Diagram("{title}", filename="{filename}", direction="{direction}", outformat="{self.output_format}", show=False, graph_attr={graph_attr}):')
        
        # Create node variable mappings
        node_vars = {}
        
        print(f"\n   🔹 [DiagramsPyRenderer] Processing {len(layers)} architectural layers:")
        
        # Generate clusters for each layer
        for layer_name in ["presentation", "application", "data", "infrastructure"]:
            if layer_name not in layers:
                continue
            
            layer_nodes = layers[layer_name]
            cluster_name = self._get_cluster_name(layer_name)
            
            print(f"      Layer '{layer_name}': {len(layer_nodes)} nodes")
            
            code_lines.append(f'    with Cluster("{cluster_name}"):')
            
            for node in layer_nodes:
                node_id = node["id"]
                label = node.get("label", "Unknown")
                icon_url = node.get("icon_url", DEFAULT_ICON)
                
                # Always use Custom with icon URL
                code_lines.append(f'        {node_id} = Custom("{label}", "{icon_url}")')
                
                print(f"         ✓ {node_id}: Custom(\"{label}\", \"{icon_url}\")")
                
                node_vars[node_id] = node_id
        
        code_lines.append("")
        
        # Generate edges
        print(f"\n   🔗 [DiagramsPyRenderer] Adding {len(edges)} edges:")
        code_lines.append("    # Define connections")
        
        for idx, edge in enumerate(edges, 1):
            if "from" not in edge or "to" not in edge:
                print(f"      ⚠️  Edge {idx} missing 'from' or 'to', skipping")
                continue
            
            from_id = edge["from"]
            to_id = edge["to"]
            label = edge.get("label", "")
            edge_type = edge.get("type", "unidirectional")
            
            if from_id not in node_vars or to_id not in node_vars:
                print(f"      ⚠️  Edge {idx} references unknown node, skipping")
                continue
            
            if edge_type == "bidirectional":
                if label:
                    code_lines.append(f'    {from_id} << Edge(label="{label}") << {to_id}')
                else:
                    code_lines.append(f'    {from_id} << {to_id}')
            else:
                if label:
                    code_lines.append(f'    {from_id} >> Edge(label="{label}") >> {to_id}')
                else:
                    code_lines.append(f'    {from_id} >> {to_id}')
            
            print(f"      {idx}. {from_id} -> {to_id} ({label if label else 'no label'})")
        
        result = "\n".join(code_lines)
        
        print(f"\n   ✅ [DiagramsPyRenderer] Code generation complete!")
        print(f"   📏 Generated {len(code_lines)} lines of Python code")
        print(f"   💾 Output will be saved as: {filename}.{self.output_format}")
        
        return result


class DrawIORenderer:
    """Renders JSON IR to Draw.io XML format."""
    
    def __init__(self, output_dir: str = "./diagrams"):
        """Initialize Draw.io renderer."""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self.node_width = 100
        self.node_height = 100
        self.x_spacing = 200
        self.y_spacing = 200
    
    def render(self, json_ir: Dict, filename: str = "architecture") -> str:
        """Convert JSON IR to Draw.io XML format."""
        print(f"\n🎨 [DrawIORenderer] Starting Draw.io XML generation")
        
        metadata = json_ir.get("diagram_metadata", {})
        nodes = json_ir.get("nodes", [])
        edges = json_ir.get("edges", [])
        
        title = metadata.get("title", "Architecture Diagram")
        
        print(f"   📊 Metadata: {title}")
        print(f"   📦 Content: {len(nodes)} nodes, {len(edges)} edges")
        
        # Group nodes by layer
        layers = {}
        layer_order = ["presentation", "application", "data", "infrastructure"]
        
        for node in nodes:
            layer = node.get("layer", "application")
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(node)
        
        # Start XML
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<mxfile host="drawio" modified="2024-01-01" agent="DrawIO" version="20.0">',
            '  <diagram name="Architecture" id="architecture_1">',
            '    <mxGraphModel dx="1000" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="900" background="#FFFFFF" math="0" shadow="0">',
            '      <root>',
            '        <mxCell id="0" />',
            '        <mxCell id="1" parent="0" />'
        ]
        
        cell_id = 2
        node_map = {}
        y_position = 50
        
        print(f"\n   🔹 [DrawIORenderer] Processing {len(layers)} layers:")
        
        # Process nodes by layer
        for layer_name in layer_order:
            if layer_name not in layers:
                continue
            
            layer_nodes = layers[layer_name]
            x_position = 50
            
            print(f"      Layer '{layer_name}': {len(layer_nodes)} nodes")
            
            # Add layer label
            xml_lines.append(f'        <mxCell id="layer_{layer_name}" value="{layer_name.replace("_", " ").title()}" style="text;fontSize=16;fontStyle=1;fillColor=none;strokeColor=none;" vertex="1" parent="1">')
            xml_lines.append(f'          <mxGeometry x="{50}" y="{y_position}" width="200" height="30" as="geometry" />')
            xml_lines.append(f'        </mxCell>')
            
            y_position += 50
            x_position = 50
            
            for node in layer_nodes:
                node_id = node["id"]
                label = node.get("label", "Unknown")
                icon_url = node.get("icon_url", DEFAULT_ICON)
                
                # Layer colors
                layer_colors = {
                    "presentation": "#E3F2FD",
                    "application": "#F3E5F5",
                    "data": "#E8F5E9",
                    "infrastructure": "#FFF3E0"
                }
                fill_color = layer_colors.get(layer_name, "#FFFFFF")
                
                # Create shape with image and text
                xml_lines.append(f'        <mxCell id="{cell_id}" value="{label}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={fill_color};strokeColor=#999999;image={icon_url};imageAspect=1;" vertex="1" parent="1">')
                xml_lines.append(f'          <mxGeometry x="{x_position}" y="{y_position}" width="{self.node_width}" height="{self.node_height}" as="geometry" />')
                xml_lines.append(f'        </mxCell>')
                
                node_map[node_id] = cell_id
                cell_id += 1
                x_position += self.x_spacing
            
            y_position += self.y_spacing
        
        print(f"\n   🔗 [DrawIORenderer] Adding {len(edges)} edges:")
        
        # Add edges
        for idx, edge in enumerate(edges, 1):
            if "from" not in edge or "to" not in edge:
                print(f"      ⚠️  Edge {idx} missing 'from' or 'to', skipping")
                continue
            
            from_id = edge["from"]
            to_id = edge["to"]
            label = edge.get("label", "")
            edge_type = edge.get("type", "unidirectional")
            
            if from_id not in node_map or to_id not in node_map:
                print(f"      ⚠️  Edge {idx} references unknown node, skipping")
                continue
            
            from_cell = node_map[from_id]
            to_cell = node_map[to_id]
            
            # Edge style
            if edge_type == "bidirectional":
                edge_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;startArrow=classic;endArrow=classic;"
            else:
                edge_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;startArrow=none;endArrow=classic;"
            
            xml_lines.append(f'        <mxCell id="edge_{cell_id}" value="{label}" style="{edge_style}" edge="1" parent="1" source="{from_cell}" target="{to_cell}">')
            xml_lines.append(f'          <mxGeometry relative="1" as="geometry" />')
            xml_lines.append(f'        </mxCell>')
            
            cell_id += 1
            print(f"      {idx}. {from_id} -> {to_id} ({label if label else 'no label'})")
        
        # Close XML
        xml_lines.extend([
            '      </root>',
            '    </mxGraphModel>',
            '  </diagram>',
            '</mxfile>'
        ])
        
        result = "\n".join(xml_lines)
        
        print(f"\n   ✅ [DrawIORenderer] XML generation complete!")
        print(f"   📏 Generated {len(xml_lines)} XML lines")
        
        return result


class D2Renderer:
    """Renders JSON IR to D2 language format."""
    
    def render(self, json_ir: Dict) -> str:
        """Convert JSON IR to D2 syntax."""
        print(f"\n🎨 [D2Renderer] Starting D2 code generation")
        
        metadata = json_ir.get("diagram_metadata", {})
        nodes = json_ir.get("nodes", [])
        edges = json_ir.get("edges", [])
        
        title = metadata.get("title", "Architecture Diagram")
        direction = metadata.get("direction", "LR")
        
        print(f"   📊 Metadata: {title}")
        print(f"   📦 Content: {len(nodes)} nodes, {len(edges)} edges")
        
        d2_lines = [
            f'title: {title}',
            f'direction: {direction.lower()}',
            ''
        ]
        
        # Layer colors for D2
        layer_colors = {
            "presentation": "#5B9BD5",
            "application": "#9B7FBD",
            "data": "#70AD47",
            "infrastructure": "#FFA500"
        }
        
        # Group nodes by layer
        layers = {}
        layer_order = ["presentation", "application", "data", "infrastructure"]
        
        for node in nodes:
            layer = node.get("layer", "application")
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(node)
        
        print(f"\n   🔹 [D2Renderer] Processing {len(layers)} layers:")
        
        # Add nodes grouped by layers
        for layer_name in layer_order:
            if layer_name not in layers:
                continue
            
            layer_nodes = layers[layer_name]
            color = layer_colors.get(layer_name, "#999999")
            
            print(f"      Layer '{layer_name}': {len(layer_nodes)} nodes")
            
            d2_lines.append(f'{layer_name.replace("_", " ").title()}: {{')
            d2_lines.append(f'  style: {{')
            d2_lines.append(f'    fill: {color}')
            d2_lines.append(f'    opacity: 0.1')
            d2_lines.append(f'  }}')
            
            for node in layer_nodes:
                node_id = node["id"]
                label = node.get("label", "Unknown")
                icon_url = node.get("icon_url", DEFAULT_ICON)
                technology = node.get("technology", "")
                
                # D2 node with icon and dynamic shape
                shape_type = node.get("shape_type", "image")
                d2_lines.append(f'  {node_id}: {{')
                d2_lines.append(f'    label: {label}')
                if shape_type and shape_type != "image":
                    d2_lines.append(f'    shape: {shape_type}')
                if technology:
                    d2_lines.append(f'    tooltip: Technology: {technology}')
                d2_lines.append(f'    icon: {icon_url}')
                d2_lines.append(f'    style: {{')
                d2_lines.append(f'      stroke: {color}')
                d2_lines.append(f'      fill: #FFFFFF')
                d2_lines.append(f'    }}')
                d2_lines.append(f'  }}')
            
            d2_lines.append(f'}}')
            d2_lines.append('')
        
        # Add edges
        print(f"\n   🔗 [D2Renderer] Adding {len(edges)} edges:")
        
        d2_lines.append('# Connections')
        for idx, edge in enumerate(edges, 1):
            if "from" not in edge or "to" not in edge:
                print(f"      ⚠️  Edge {idx} missing 'from' or 'to', skipping")
                continue
            
            from_id = edge["from"]
            to_id = edge["to"]
            label = edge.get("label", "")
            edge_type = edge.get("type", "unidirectional")
            
            if edge_type == "bidirectional":
                arrow = "<->"
            else:
                arrow = "->"
            
            if label:
                d2_lines.append(f'{from_id} {arrow} {to_id}: {label}')
            else:
                d2_lines.append(f'{from_id} {arrow} {to_id}')
            
            print(f"      {idx}. {from_id} {arrow} {to_id} ({label if label else 'no label'})")
        
        result = "\n".join(d2_lines)
        
        print(f"\n   ✅ [D2Renderer] D2 generation complete!")
        print(f"   📏 Generated {len(d2_lines)} lines of D2 code")
        
        return result


class D3Renderer:
    """Renders JSON IR to D3.js compatible JSON format for force-directed graph visualization."""
    
    def render(self, json_ir: Dict) -> Dict:
        """Convert JSON IR to D3 force graph JSON format."""
        print(f"\n🎨 [D3Renderer] Starting D3.js JSON generation")
        
        metadata = json_ir.get("diagram_metadata", {})
        nodes = json_ir.get("nodes", [])
        edges = json_ir.get("edges", [])
        
        title = metadata.get("title", "Architecture Diagram")
        
        print(f"   📊 Metadata: {title}")
        print(f"   📦 Content: {len(nodes)} nodes, {len(edges)} edges")
        
        # Layer colors for D3
        layer_colors = {
            "presentation": "#5B9BD5",
            "application": "#9B7FBD",
            "data": "#70AD47",
            "infrastructure": "#FFA500"
        }
        
        # Convert nodes to D3 format
        d3_nodes = []
        node_id_map = {node["id"]: idx for idx, node in enumerate(nodes)}
        
        print(f"\n   🔹 [D3Renderer] Processing {len(nodes)} nodes:")
        
        for idx, node in enumerate(nodes):
            layer = node.get("layer", "application")
            d3_node = {
                "id": node["id"],
                "label": node.get("label", "Unknown"),
                "technology": node.get("technology", ""),
                "icon": node.get("icon_url", DEFAULT_ICON),
                "layer": layer,
                "color": layer_colors.get(layer, "#999999"),
                "group": layer,
                "index": idx
            }
            d3_nodes.append(d3_node)
            print(f"      {idx + 1}. {node['id']}: {node.get('label', 'Unknown')}")
        
        # Convert edges to D3 format
        d3_links = []
        
        print(f"\n   🔗 [D3Renderer] Processing {len(edges)} edges:")
        
        for idx, edge in enumerate(edges, 1):
            if "from" not in edge or "to" not in edge:
                print(f"      ⚠️  Edge {idx} missing 'from' or 'to', skipping")
                continue
            
            from_id = edge["from"]
            to_id = edge["to"]
            
            if from_id not in node_id_map or to_id not in node_id_map:
                print(f"      ⚠️  Edge {idx} references unknown node, skipping")
                continue
            
            d3_link = {
                "source": node_id_map[from_id],
                "target": node_id_map[to_id],
                "label": edge.get("label", ""),
                "type": edge.get("type", "unidirectional"),
                "value": 1
            }
            d3_links.append(d3_link)
            print(f"      {idx}. {from_id} -> {to_id}")
        
        # Combine into D3 graph format
        d3_graph = {
            "title": title,
            "nodes": d3_nodes,
            "links": d3_links,
            "metadata": {
                "nodeCount": len(d3_nodes),
                "linkCount": len(d3_links),
                "layers": list(set(node.get("layer", "application") for node in nodes))
            }
        }
        
        print(f"\n   ✅ [D3Renderer] D3 JSON generation complete!")
        print(f"   📏 Generated {len(d3_nodes)} nodes and {len(d3_links)} links")
        
        return d3_graph

        
class MermaidRenderer:
    """Renders JSON IR to Mermaid v11+ syntax with enhanced styling."""
    
    def __init__(self, icon_size: int = 48, node_padding: int = 20, enable_styling: bool = True):
        """
        Initialize renderer with styling options.
        
        Args:
            icon_size: Size of icons in pixels (default: 48)
            node_padding: Padding around nodes in pixels (default: 20)
            enable_styling: Whether to add custom CSS styling (default: True)
        """
        self.icon_size = icon_size
        self.node_padding = node_padding
        self.enable_styling = enable_styling
    
    def render(self, json_ir: Dict) -> str:
        """Convert JSON IR to Mermaid diagram with enhanced styling."""
        print(f"\n🎨 [MermaidRenderer] Starting Mermaid rendering")
        print(f"   ⚙️  Icon Size: {self.icon_size}px")
        print(f"   ⚙️  Node Padding: {self.node_padding}px")
        print(f"   ⚙️  Custom Styling: {'Enabled' if self.enable_styling else 'Disabled'}")
        
        metadata = json_ir.get("diagram_metadata", {})
        nodes = json_ir.get("nodes", [])
        edges = json_ir.get("edges", [])
        
        direction = metadata.get("direction", "LR")
        title = metadata.get("title", "Architecture Diagram")
        
        print(f"   📊 Metadata:")
        print(f"      Title: {title}")
        print(f"      Direction: {direction}")
        print(f"   📦 Content: {len(nodes)} nodes, {len(edges)} edges")
        
        mermaid_lines = [
            f"---",
            f"title: {title}",
            f"---",
            f"graph {direction}"
        ]
        
        # Add nodes with icons
        print(f"\n   🔹 [MermaidRenderer] Adding nodes to diagram:")
        for idx, node in enumerate(nodes, 1):
            node_id = node["id"]
            label = node.get("label", "Unknown")
            icon_url = node.get("icon_url", DEFAULT_ICON)
            
            print(f"      {idx}. {node_id}: '{label}' with icon {icon_url}")
            
            # Mermaid v11+ syntax with image and custom dimensions
            mermaid_lines.append(
                f'    {node_id}@{{ img: "{icon_url}", label: "{label}", w: {self.icon_size}, h: {self.icon_size} }}'
            )
        
        # Add edges
        print(f"\n   🔗 [MermaidRenderer] Adding edges to diagram:")
        for idx, edge in enumerate(edges, 1):
            # Validate edge has required fields
            if "from" not in edge or "to" not in edge:
                print(f"      ⚠️  Edge {idx} missing 'from' or 'to' field, skipping: {edge}")
                continue
            
            from_id = edge["from"]
            to_id = edge["to"]
            label = edge.get("label", "")
            edge_type = edge.get("type", "unidirectional")
            
            if edge_type == "bidirectional":
                arrow = "<-->"
            else:
                arrow = "-->"
            
            if label:
                edge_repr = f'{from_id} {arrow}|"{label}"| {to_id}'
                mermaid_lines.append(f"    {edge_repr}")
                print(f"      {idx}. {edge_repr}")
            else:
                edge_repr = f"{from_id} {arrow} {to_id}"
                mermaid_lines.append(f"    {edge_repr}")
                print(f"      {idx}. {edge_repr}")
        
        # Add layer-based styling (color-code by architectural layer)
        if self.enable_styling:
            print(f"\n   🎨 [MermaidRenderer] Adding custom styling:")
            mermaid_lines.append(f"\n    %% Custom Styling")
            
            layer_styles = {
                "presentation": {"fill": "#e3f2fd", "stroke": "#1976d2", "color": "#1976d2"},
                "application": {"fill": "#f3e5f5", "stroke": "#7b1fa2", "color": "#7b1fa2"},
                "data": {"fill": "#e8f5e9", "stroke": "#388e3c", "color": "#388e3c"},
                "infrastructure": {"fill": "#fff3e0", "stroke": "#f57c00", "color": "#f57c00"}
            }
            
            for node in nodes:
                node_id = node["id"]
                layer = node.get("layer", "application")
                style = layer_styles.get(layer, layer_styles["application"])
                
                style_str = f"fill:{style['fill']},stroke:{style['stroke']},stroke-width:2px,color:{style['color']}"
                mermaid_lines.append(f"    style {node_id} {style_str}")
                print(f"      Applied '{layer}' layer style to {node_id}")
        
        result = "\n".join(mermaid_lines)
        print(f"\n   ✅ [MermaidRenderer] Rendering complete!")
        print(f"   📏 Output length: {len(result)} characters")
        
        return result


class DiagramGenerationPipeline:
    """Main orchestrator for the diagram generation system."""
    
    def __init__(
        self, 
        icon_size: int = 48, 
        node_padding: int = 20, 
        enable_styling: bool = True,
        diagrams_format: str = "png",
        output_dir: str = "./diagrams"
    ):
        """
        Initialize pipeline with rendering options.
        
        Args:
            icon_size: Size of icons in pixels for Mermaid (default: 48)
            node_padding: Padding around nodes in pixels (default: 20)
            enable_styling: Whether to add layer-based color styling (default: True)
            diagrams_format: Output format for Diagrams.py (png, jpg, svg, pdf)
            output_dir: Directory to save Diagrams.py output
        """
        self.planner = PlannerAgent(LITELLM_CONFIG)
        self.auditor = AuditorAgent(LITELLM_CONFIG)
        self.icon_resolver = IconResolver()
        self.mermaid_renderer = MermaidRenderer(
            icon_size=icon_size,
            node_padding=node_padding,
            enable_styling=enable_styling
        )
        self.diagrams_renderer = DiagramsPyRenderer(
            output_format=diagrams_format,
            output_dir=output_dir
        )
        print(f"🏗️  [Pipeline] Initialized with:")
        print(f"    • Mermaid: icon_size={icon_size}px, styling={'ON' if enable_styling else 'OFF'}")
        print(f"    • Diagrams.py: format={diagrams_format}, output_dir={output_dir}")
    
    def generate(self, user_input: str, max_iterations: int = 2) -> Dict:
        """
        Generate architecture diagram from natural language.
        
        Returns:
            {
                "json_ir": {...},
                "mermaid": "...",
                "suggestions": [...],
                "iterations": 1
            }
        """
        print(f"\n{'='*80}")
        print(f"🚀 [Pipeline] STARTING DIAGRAM GENERATION PIPELINE")
        print(f"{'='*80}")
        print(f"📝 User Input: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")
        print(f"⚙️  Max Iterations: {max_iterations}")
        print(f"{'='*80}\n")
        
        # Step 1: Planner extracts architecture
        print(f"╔════════════════════════════════════════════════════════════════════════════╗")
        print(f"║ STEP 1: PLANNING - Extracting Architecture from User Input                ║")
        print(f"╚════════════════════════════════════════════════════════════════════════════╝")
        json_ir = self.planner.extract_architecture(user_input)
        print(f"\n✅ Planning complete! Generated IR with {len(json_ir.get('nodes', []))} nodes\n")
        
        # Step 2: Resolve icons
        print(f"╔════════════════════════════════════════════════════════════════════════════╗")
        print(f"║ STEP 2: ICON RESOLUTION - Finding Icons for Technologies                  ║")
        print(f"╚════════════════════════════════════════════════════════════════════════════╝")
        node_count = len(json_ir.get('nodes', []))
        print(f"🎨 Resolving icons for {node_count} component(s)...")
        json_ir["nodes"] = self.icon_resolver.resolve_icons(json_ir.get("nodes", []))
        print(f"✅ Icon resolution complete!\n")
        
        # Step 3: Auditor reviews (with iteration support)
        print(f"╔════════════════════════════════════════════════════════════════════════════╗")
        print(f"║ STEP 3: AUDITING - Reviewing Architecture for Best Practices              ║")
        print(f"╚════════════════════════════════════════════════════════════════════════════╝")
        
        suggestions = []
        iteration = 0
        
        while iteration < max_iterations:
            print(f"\n{'─'*80}")
            print(f"🔄 AUDIT ITERATION {iteration + 1}/{max_iterations}")
            print(f"{'─'*80}")
            
            is_valid, audit_suggestions, corrected_ir = self.auditor.audit(json_ir)
            
            suggestions.extend(audit_suggestions)
            
            print(f"\n   📊 Audit Result: {'✅ VALID' if is_valid else '❌ NEEDS CORRECTION'}")
            print(f"   💡 Suggestions received: {len(audit_suggestions)}")
            
            if is_valid or corrected_ir is None:
                print(f"   ✓ Design approved or no corrections needed")
                break
            
            # Use corrected IR and re-resolve icons
            print(f"\n   🔄 Applying corrections from auditor...")
            print(f"   📦 Corrected IR has {len(corrected_ir.get('nodes', []))} nodes")
            json_ir = corrected_ir
            
            print(f"   🎨 Re-resolving icons for corrected architecture...")
            json_ir["nodes"] = self.icon_resolver.resolve_icons(json_ir.get("nodes", []))
            
            iteration += 1
            print(f"   ✅ Iteration {iteration} complete")
        
        print(f"\n{'─'*80}")
        print(f"✅ Auditing phase complete after {iteration + 1} iteration(s)")
        print(f"{'─'*80}\n")
        
        # Step 4: Render to Mermaid
        print(f"╔════════════════════════════════════════════════════════════════════════════╗")
        print(f"║ STEP 4: RENDERING - Converting to Multiple Diagram Formats                ║")
        print(f"╚════════════════════════════════════════════════════════════════════════════╝")
        
        print(f"\n   📊 [Pipeline] Rendering to Mermaid format...")
        mermaid_code = self.mermaid_renderer.render(json_ir)
        
        print(f"\n   🐍 [Pipeline] Generating Diagrams.py code...")
        diagrams_code = self.diagrams_renderer.render(json_ir)

        # Add these new renderers
        drawio_xml = DrawIORenderer().render(json_ir)
        d2_code = D2Renderer().render(json_ir)
        d3_json = D3Renderer().render(json_ir)
        
        result = {
            "json_ir": json_ir,
            "mermaid": mermaid_code,
            "diagrams_py": diagrams_code,
            "drawio_xml": drawio_xml,
            "d2_code": d2_code,
            "d3_json": d3_json,
            "suggestions": suggestions,
            "iterations": iteration + 1
        }
        
        print(f"\n{'='*80}")
        print(f"🎉 [Pipeline] DIAGRAM GENERATION COMPLETE!")
        print(f"{'='*80}")
        print(f"📊 Final Statistics:")
        print(f"   • Nodes: {len(json_ir.get('nodes', []))}")
        print(f"   • Edges: {len(json_ir.get('edges', []))}")
        print(f"   • Suggestions: {len(suggestions)}")
        print(f"   • Total Iterations: {iteration + 1}")
        print(f"   • Mermaid Output: {len(mermaid_code)} characters")
        print(f"   • Diagrams.py Code: {len(diagrams_code)} characters")
        print(f"   • DrawIO XML: {len(drawio_xml)} characters")
        print(f"   • D2 Code: {len(d2_code)} characters")
        print(f"   • D3 JSON: {len(d3_json)} characters")
        print(f"{'='*80}\n")
        
        return result


# Example Usage
if __name__ == "__main__":
    print(f"\n{'#'*80}")
    print(f"#{'ARCHITECTURE DIAGRAM GENERATOR - COMPREHENSIVE DEBUG MODE'.center(78)}#")
    print(f"{'#'*80}\n")
    
    pipeline = DiagramGenerationPipeline()
    
    # Example 1: Simple web app
    user_request = """
    Build a web application with:
    - React frontend
    - Node.js backend API
    - PostgreSQL database
    - Redis for caching
    - Deploy on AWS with S3 for static assets
    """
    
    print(f"📋 Test Case: Web Application Architecture")
    print(f"{'─'*80}\n")
    
    result = pipeline.generate(user_request)
    with open("output.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"📊 FINAL OUTPUT - JSON IR")
    print(f"{'='*80}")
    print(json.dumps(result["json_ir"], indent=2))
    
    print(f"\n{'='*80}")
    print(f"🎨 FINAL OUTPUT - MERMAID DIAGRAM CODE")
    print(f"{'='*80}")
    print(result["mermaid"])
    
    print(f"\n{'='*80}")
    print(f"💡 ARCHITECTURE SUGGESTIONS")
    print(f"{'='*80}")
    if result["suggestions"]:
        for i, suggestion in enumerate(result["suggestions"], 1):
            print(f"{i}. {suggestion}")
    else:
        print("No suggestions provided.")
    
    print(f"\n{'='*80}")
    print(f"📈 PIPELINE STATISTICS")
    print(f"{'='*80}")
    print(f"🔄 Total Iterations: {result['iterations']}")
    print(f"📦 Total Nodes: {len(result['json_ir'].get('nodes', []))}")
    print(f"🔗 Total Edges: {len(result['json_ir'].get('edges', []))}")
    print(f"💬 Total Suggestions: {len(result['suggestions'])}")
    print(f"📏 Mermaid Output Size: {len(result['mermaid'])} characters")
    print(f"\n{'#'*80}")
    print(f"#{'GENERATION COMPLETE'.center(78)}#")
    print(f"{'#'*80}\n")