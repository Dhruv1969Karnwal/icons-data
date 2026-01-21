from typing import Dict
from mermaid.config import LITELLM_CONFIG
from mermaid.agents.planner import PlannerAgent
from mermaid.agents.auditor import AuditorAgent
from mermaid.utils.icon_resolver import IconResolver
from mermaid.renderers.mermaid_renderer import MermaidRenderer
from mermaid.renderers.diagramspy import DiagramsPyRenderer
from mermaid.renderers.drawio import DrawIORenderer
from mermaid.renderers.d2 import D2Renderer
from mermaid.renderers.d3 import D3Renderer

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
    
    def generate(self, user_input: str, max_iterations: int = 0) -> Dict:
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
