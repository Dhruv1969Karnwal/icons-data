import math
from pathlib import Path
from typing import Dict

class DrawIORenderer:
    """
    Renders dynamic, grid-aware architecture diagrams for Draw.io.
    Supports SVG icons, smart orthogonal routing, and multi-layer clustering.
    """
    
    def __init__(self, output_dir: str = "./diagrams"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # UI & Spacing Configuration
        self.node_w = 130      # Width of each service box
        self.node_h = 100      # Height (taller to fit Icon + Text)
        self.x_gap = 70        # Horizontal spacing between nodes
        self.y_gap = 60        # Vertical spacing between nodes within a layer
        self.max_cols = 4      # Number of nodes before wrapping to a new row
        self.canvas_center = 1000  # Horizontal midpoint of the diagram
        
        # Default Icon if JSON is missing one
        self.default_icon = "https://img.icons8.com/color/96/cloud--v1.png"

    def render(self, json_ir: Dict, filename: str = "architecture_output") -> str:
        nodes = json_ir.get("nodes", [])
        edges = json_ir.get("edges", [])
        
        # 1. Group nodes by layer and define strict vertical order
        layers = {}
        layer_order = ["security", "presentation", "infrastructure", "application", "data", "devops"]
        
        for node in nodes:
            l_name = node.get("layer", "application").lower()
            if l_name not in layers:
                layers[l_name] = []
            layers[l_name].append(node)

        # 2. Modern Color Palette
        layer_styles = {
            "security": "#D32F2F",       # Red
            "presentation": "#1976D2",   # Blue
            "infrastructure": "#F57C00", # Orange
            "application": "#7B1FA2",    # Purple
            "data": "#388E3C",           # Green
            "devops": "#455A64"          # Blue-Grey
        }

        # XML Boilerplate
        xml = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<mxfile host="app.diagrams.net" version="21.0">',
            '  <diagram name="Cloud Architecture" id="arch_pro">',
            '    <mxGraphModel dx="2000" dy="1200" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" background="#F8F9FA">',
            '      <root>',
            '        <mxCell id="0" />',
            '        <mxCell id="1" parent="0" />'
        ]

        node_map = {}
        cell_id = 100
        current_y = 60  # Starting vertical position

        # 3. Process Layers into Grid-based Swimlanes
        for layer_name in layer_order:
            if layer_name not in layers:
                continue
            
            layer_nodes = layers[layer_name]
            color = layer_styles.get(layer_name, "#424242")
            
            # Calculate Grid Dimensions
            num_nodes = len(layer_nodes)
            cols = min(num_nodes, self.max_cols)
            rows = math.ceil(num_nodes / self.max_cols)
            
            # Calculate Swimlane Size
            zone_w = (cols * self.node_w) + ((cols + 1) * self.x_gap)
            zone_h = (rows * self.node_h) + ((rows + 1) * self.y_gap) + 20
            zone_x = self.canvas_center - (zone_w / 2)

            # Draw Layer Container (Swimlane)
            z_id = f"zone_{layer_name}"
            # 0D at the end of color hex makes it ~5% transparent for the background fill
            swimlane_style = (f"swimlane;whiteSpace=wrap;html=1;startSize=30;collapsible=0;dashed=1;"
                              f"strokeColor={color};fillColor={color}0D;fontColor={color};fontStyle=1;")
            
            xml.append(f'        <mxCell id="{z_id}" value="{layer_name.upper()} LAYER" style="{swimlane_style}" vertex="1" parent="1">')
            xml.append(f'          <mxGeometry x="{zone_x}" y="{current_y}" width="{zone_w}" height="{zone_h}" as="geometry" />')
            xml.append(f'        </mxCell>')

            # 4. Add Nodes into the Grid
            for idx, node in enumerate(layer_nodes):
                r = idx // self.max_cols
                c = idx % self.max_cols
                
                # Logic to center nodes in partially filled rows
                nodes_in_this_row = min(self.max_cols, num_nodes - (r * self.max_cols))
                row_offset = (zone_w - (nodes_in_this_row * (self.node_w + self.x_gap) - self.x_gap)) / 2

                nx = row_offset + (c * (self.node_w + self.x_gap))
                ny = 55 + (r * (self.node_h + self.y_gap))

                # Extract SVG URL and generate Label
                icon = node.get("icon_url", self.default_icon)
                label = f"&lt;b&gt;{node['label']}&lt;/b&gt;&lt;br/&gt;&lt;small&gt;{node.get('technology','')}&lt;/small&gt;"
                
                # Shape Label Style: supports SVG image at top, text at bottom
                node_style = (f"shape=label;whiteSpace=wrap;html=1;image={icon};imageWidth=40;imageHeight=40;"
                              f"fillColor=#ffffff;strokeColor={color};strokeWidth=2;verticalAlign=bottom;spacingBottom=10;"
                              f"imageAlign=center;imageVerticalAlign=top;spacingTop=45;rounded=1;arcSize=10;glass=0;")
                
                xml.append(f'        <mxCell id="{cell_id}" value="{label}" style="{node_style}" vertex="1" parent="{z_id}">')
                xml.append(f'          <mxGeometry x="{nx}" y="{ny}" width="{self.node_w}" height="{self.node_h}" as="geometry" />')
                xml.append(f'        </mxCell>')
                
                node_map[node["id"]] = cell_id
                cell_id += 1
            
            # Update Y-offset for next layer with breathing room
            current_y += zone_h + 100

        # 5. Smart Edge Rendering (Orthogonal + Rounded)
        for edge in edges:
            src_id = node_map.get(edge["from"])
            tgt_id = node_map.get(edge["to"])
            
            if src_id and tgt_id:
                label = edge.get("label", "")
                # curviness=12 gives modern rounded corners to the lines
                edge_style = ("edgeStyle=orthogonalEdgeStyle;rounded=1;curviness=12;html=1;"
                              "strokeColor=#546E7A;strokeWidth=1.5;fontSize=10;fontColor=#37474F;"
                              "endArrow=block;endFill=1;jettySize=auto;orthogonalLoop=1;")
                
                xml.append(f'        <mxCell id="{cell_id}" value="{label}" style="{edge_style}" edge="1" parent="1" source="{src_id}" target="{tgt_id}">')
                xml.append(f'          <mxGeometry relative="1" as="geometry"><mxPoint as="offset" /></mxGeometry>')
                xml.append(f'        </mxCell>')
                cell_id += 1

        # Close XML
        xml.extend(['      </root>', '    </mxGraphModel>', '  </diagram>', '</mxfile>'])
        return "\n".join(xml)

# --- EXAMPLE USAGE ---
# renderer = DrawIORenderer()
# xml_output = renderer.render(your_json_ir)
# with open("diagram.drawio", "w") as f:
#     f.write(xml_output)