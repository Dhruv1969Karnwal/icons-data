from typing import Dict
from mermaid.config import DEFAULT_ICON

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
