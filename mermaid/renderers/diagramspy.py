from pathlib import Path
from typing import Dict
from mermaid.config import DEFAULT_ICON

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
