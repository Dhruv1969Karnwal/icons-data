from typing import Dict, List, Optional
from mermaid.config import DEFAULT_ICON

class MermaidRenderer:
    """Renders JSON IR to Mermaid v11+ syntax with UI/UX-focused enhancements."""
    
    def __init__(
        self,
        icon_size: int = 48,
        node_padding: int = 20,
        enable_styling: bool = True,
        max_nodes_per_diagram: int = 12,
        responsive_mode: bool = True,
        add_legend: bool = True,
        edge_labels_enabled: bool = True
    ):
        """
        Initialize renderer with UI/UX-focused options.
        
        Args:
            icon_size: Size of icons in pixels
            node_padding: Padding around nodes
            enable_styling: Custom CSS styling
            max_nodes_per_diagram: Threshold for splitting into multiple diagrams
            responsive_mode: Optimize for different screen sizes
            add_legend: Include legend explaining color scheme
            edge_labels_enabled: Show labels on connections
        """
        self.icon_size = icon_size
        self.node_padding = node_padding
        self.enable_styling = enable_styling
        self.max_nodes_per_diagram = max_nodes_per_diagram
        self.responsive_mode = responsive_mode
        self.add_legend = add_legend
        self.edge_labels_enabled = edge_labels_enabled
        
        self.layer_styles = {
            "presentation": {"fill": "#e3f2fd", "stroke": "#1976d2", "color": "#1976d2", "label": "UI/Frontend"},
            "application": {"fill": "#f3e5f5", "stroke": "#7b1fa2", "color": "#7b1fa2", "label": "Services"},
            "data": {"fill": "#e8f5e9", "stroke": "#388e3c", "color": "#388e3c", "label": "Data Layer"},
            "infrastructure": {"fill": "#fff3e0", "stroke": "#f57c00", "color": "#f57c00", "label": "Infrastructure"},
            "security": {"fill": "#ffebee", "stroke": "#c62828", "color": "#c62828", "label": "Security"},
            "operations": {"fill": "#eceff1", "stroke": "#455a64", "color": "#455a64", "label": "Operations"}
        }
    
    def _should_split_diagram(self, nodes: List) -> bool:
        """Determine if diagram should be split for readability."""
        return len(nodes) > self.max_nodes_per_diagram
    
    def _get_critical_path_nodes(self, json_ir: Dict) -> set:
        """Identify critical path components (high in/out degree)."""
        nodes = json_ir.get("nodes", [])
        edges = json_ir.get("edges", [])
        
        # Count node connections
        node_degrees = {node["id"]: 0 for node in nodes}
        for edge in edges:
            if "from" in edge and "to" in edge:
                node_degrees[edge["from"]] = node_degrees.get(edge["from"], 0) + 1
                node_degrees[edge["to"]] = node_degrees.get(edge["to"], 0) + 1
        
        # Top 30% most connected nodes are critical
        sorted_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)
        critical_count = max(1, len(sorted_nodes) // 3)
        return {node_id for node_id, _ in sorted_nodes[:critical_count]}
    
    # def _create_legend(self) -> List[str]:
    #     """Generate legend explaining color scheme and layers."""
    #     legend_lines = []
        
    #     # Style legend nodes
    #     for layer_key, layer_name in [
    #         ("presentation", "leg_presentation"),
    #         ("application", "leg_services"),
    #         ("data", "leg_data"),
    #         ("infrastructure", "leg_infra"),
    #         ("security", "leg_security"),
    #         ("operations", "leg_ops")
    #     ]:
    #         style = self.layer_styles.get(layer_key, self.layer_styles["application"])
    #         style_str = f"fill:{style['fill']},stroke:{style['stroke']},stroke-width:2px,color:{style['color']}"
    #         legend_lines.append(f"    style {layer_name} {style_str}")
        
    #     return legend_lines
    
    def _optimize_edge_labels(self, edges: List[Dict]) -> List[Dict]:
        """Reduce edge label clutter by grouping similar connections."""
        if not self.edge_labels_enabled:
            return [e for e in edges if "label" not in e or e["label"] == ""]
        
        # Group edges by relationship type
        grouped = {}
        for edge in edges:
            key = (edge.get("from"), edge.get("to"))
            label = edge.get("label", "")
            edge_type = edge.get("type", "unidirectional")
            
            if key not in grouped:
                grouped[key] = {"edge": edge, "labels": []}
            
            if label:
                grouped[key]["labels"].append(label)
        
        # Deduplicate and limit labels
        optimized = []
        for (from_id, to_id), data in grouped.items():
            edge = data["edge"].copy()
            if data["labels"]:
                # Show only first unique label to reduce clutter
                edge["label"] = data["labels"][0]
            optimized.append(edge)
        
        return optimized
    
    def _enhance_node_styling(self, node: Dict, critical_nodes: set) -> str:
        """Create enhanced styling for individual nodes."""
        node_id = node["id"]
        layer = node.get("layer", "application")
        style = self.layer_styles.get(layer, self.layer_styles["application"])
        
        # Emphasize critical path nodes
        if node_id in critical_nodes:
            stroke_width = "3px"
            style_str = f"fill:{style['fill']},stroke:{style['stroke']},stroke-width:{stroke_width},color:{style['color']}"
        else:
            stroke_width = "2px"
            style_str = f"fill:{style['fill']},stroke:{style['stroke']},stroke-width:{stroke_width},color:{style['color']}"
        
        return f"    style {node_id} {style_str}"
    
    def render(self, json_ir: Dict) -> str:
        """Convert JSON IR to optimized Mermaid diagram."""
        print(f"\n[MermaidRenderer] Starting render with UI/UX optimizations")
        print(f"   - Responsive Mode: {self.responsive_mode}")
        print(f"   - Legend Enabled: {self.add_legend}")
        print(f"   - Edge Label Optimization: {self.edge_labels_enabled}")
        
        metadata = json_ir.get("diagram_metadata", {})
        nodes = json_ir.get("nodes", [])
        edges = json_ir.get("edges", [])
        
        direction = metadata.get("direction", "LR")
        title = metadata.get("title", "Architecture Diagram")
        
        # Get critical path for emphasis
        critical_nodes = self._get_critical_path_nodes(json_ir)
        print(f"   * Identified {len(critical_nodes)} critical path components")
        
        # Optimize edges
        optimized_edges = self._optimize_edge_labels(edges)
        print(f"   - Edge optimization: {len(edges)} -> {len(optimized_edges)} (reduced clutter)")
        
        mermaid_lines = [
            f"---",
            f"title: {title}",
            f"---",
            f"graph {direction}",
            "",
            "    %% Configuration for better rendering",
            "    %%{init: {'flowchart': {'useMaxWidth': true, 'htmlLabels': true}}}%%"
        ]
        
        # Group nodes by layer
        layers = {}
        for node in nodes:
            layer = node.get("layer", "application")
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(node)
        
        print(f"\n   - Processing {len(layers)} layers:")
        
        # Add nodes grouped by layer (subgraphs)
        for layer_name, layer_nodes in layers.items():
            subgraph_title = self.layer_styles.get(layer_name, {}).get("label", layer_name.title())
            mermaid_lines.append(f"\n    subgraph {layer_name} [ {subgraph_title} ]")
            
            for node in layer_nodes:
                node_id = node["id"]
                label = node.get("label", "Unknown")
                icon_url = node.get("icon_url", DEFAULT_ICON)
                
                icon_html = f"<img src='{icon_url}' width='{self.icon_size}'/>"
                node_definition = f'        {node_id}["{icon_html}<br/>{label}"]'
                mermaid_lines.append(node_definition)
            
            mermaid_lines.append("    end")
        
        # Add edges (optimized)
        print(f"\n   - Adding {len(optimized_edges)} edges:")
        for edge in optimized_edges:
            if "from" not in edge or "to" not in edge:
                continue
            
            from_id = edge["from"]
            to_id = edge["to"]
            label = edge.get("label", "")
            edge_type = edge.get("type", "unidirectional")
            
            arrow = "<-->" if edge_type == "bidirectional" else "-->"
            
            if label:
                mermaid_lines.append(f'    {from_id} {arrow}|"{label}"| {to_id}')
            else:
                mermaid_lines.append(f"    {from_id} {arrow} {to_id}")
        
        # Add styling
        if self.enable_styling:
            mermaid_lines.append(f"\n    %% Node Styling (critical path emphasized)")
            for node in nodes:
                style_line = self._enhance_node_styling(node, critical_nodes)
                mermaid_lines.append(style_line)
        
        # Add legend
        # if self.add_legend:
        #     mermaid_lines.extend(self._create_legend())
        
        result = "\n".join(mermaid_lines)
        print(f"\n   [OK] Rendering complete!")
        print(f"   - Output length: {len(result)} characters")
        print(f"   - Diagram Stats: {len(nodes)} nodes, {len(optimized_edges)} edges, {len(critical_nodes)} critical")
        
        return result


