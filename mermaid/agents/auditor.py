import json
from typing import Dict, List, Optional, Tuple
from litellm import completion
from mermaid.utils.json_helper import robust_json_loads

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
        
        system_prompt = """You are a senior solutions architect reviewing a system design.
Review the provided architecture for:
1. Missing critical components (load balancers, caching, monitoring)
2. Security concerns (exposed databases, missing authentication)
3. Scalability issues (single points of failure)
4. Best practices violations
5. Logical inconsistencies in connections

Provide your response in this JSON format:
{
  "is_valid": true/false,
  "suggestions": ["suggestion 1", "suggestion 2"],
  "severity": "low|medium|high",
  "corrected_ir": null // or the full IR if is_valid is false
}

If the design is fundamentally sound, set is_valid to true and provide minor suggestions.
If there are critical issues, set is_valid to false and provide a full corrected_ir.

CRITICAL REQUIREMENTS FOR corrected_ir:
1. Must include "technology" field for every node (e.g., "nodejs", "postgresql", "redis")
2. Every edge must have "from", "to", "label", and "type" fields
3. Edge format: {"from": "node_id", "to": "node_id", "label": "connection", "type": "unidirectional"}
4. DO NOT use placeholders like "..." in the JSON. Provide complete data.
5. Your response must contain ONLY the JSON object, nothing else. No explanations before or after."""

        user_prompt = f"Current Design (JSON IR):\n{json.dumps(json_ir, indent=2)}\n\nReview this architecture and provide the response:"

        print(f"   📤 [AuditorAgent] Sending audit request to LLM...")
        print(f"   ⚙️  Model: {self.config['model']}")
        
        try:
            response = completion(
                model=self.config["model"],
                api_base=self.config["base_url"],
                api_key=self.config["api_key"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                # request_timeout=30  # Add 30s timeout
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
            
            print(f"   🔍 [AuditorAgent] Parsing audit result JSON...")
            audit_result = robust_json_loads(content)
            
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
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"   ❌ [AuditorAgent] JSON parsing error in audit result: {e}")
            if 'content' in locals() and len(content) < 1000:
                print(f"   📄 Content that failed to parse:\n{content}")
            print(f"   🔄 Proceeding with original design")
            return True, ["Audit failed, proceeding with original design"], None
        except Exception as e:
            print(f"   ❌ [AuditorAgent] Unexpected error during audit: {type(e).__name__}: {e}")
            import traceback
            print(f"   📍 Traceback:\n{traceback.format_exc()}")
            return True, ["Audit failed, proceeding with original design"], None
