import json
import re
from typing import Dict, Optional

def robust_json_loads(content: str) -> Dict:
    """
    Robustly parse JSON from LLM output.
    Handles thinking blocks, excessive preamble, markdown formatting, trailing commas, and extra data.
    """
    if not content:
        return {}

    # 1. Strip <think> blocks if present
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

    # 2. Pre-processing: Try to clean common JSON-breaking patterns
    def clean_json_str(s):
        # Remove trailing commas in objects and arrays
        s = re.sub(r',\s*([\]}])', r'\1', s)
        return s

    # 3. Try direct parsing first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        try:
            return json.loads(clean_json_str(content))
        except json.JSONDecodeError:
            pass

    # 4. Detect and extract from markdown code blocks
    if "```json" in content:
        try:
            json_block = content.split("```json")[1].split("```")[0].strip()
            return json.loads(clean_json_str(json_block))
        except (IndexError, json.JSONDecodeError):
            pass
    elif "```" in content:
        try:
            blocks = re.findall(r'```(?:[a-zA-Z]+)?\n?(.*?)\n?```', content, re.DOTALL)
            for block in blocks:
                try:
                    return json.loads(clean_json_str(block.strip()))
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

    # 5. Use raw_decode to handle "Extra data" (text after JSON)
    # We search for the first '{' and try to decode from there
    for match in re.finditer(r'\{', content):
        start_idx = match.start()
        potential_json = content[start_idx:]
        try:
            # raw_decode returns (result, index) where index is where it stopped parsing
            decoder = json.JSONDecoder()
            result, end = decoder.raw_decode(potential_json)
            return result
        except json.JSONDecodeError:
            # Try cleaning trailing commas and decode again
            # This is tricky with raw_decode, so we'll rely on brace matching for cleaned content
            pass

    # 6. Last resort: Find the largest matching { ... } block
    # This is helpful if there's text before AND after the JSON
    try:
        best_match = ""
        stack = 0
        current_start = -1
        
        for i, char in enumerate(content):
            if char == '{':
                if stack == 0:
                    current_start = i
                stack += 1
            elif char == '}':
                stack -= 1
                if stack == 0 and current_start != -1:
                    candidate = content[current_start:i+1]
                    # We want the longest valid-looking JSON object
                    if len(candidate) > len(best_match):
                        try:
                            return json.loads(clean_json_str(candidate))
                        except json.JSONDecodeError:
                            # If it failed, maybe it's still the best we have, but keep looking
                            try:
                                # One more try: just check if it has "nodes" and "edges"
                                if '"nodes"' in candidate and '"edges"' in candidate:
                                    # Try to fix truncated JSON if it ends abruptly
                                    fixed = clean_json_str(candidate)
                                    # If it's still failing, we can't do much here without more complex logic
                                    json.loads(fixed)
                                    best_match = fixed
                            except json.JSONDecodeError:
                                pass
        
        if best_match:
            return json.loads(best_match)
    except Exception:
        pass

    # 7. Heavy-duty search for key markers (fallback if brace matching fails)
    if '"nodes"' in content and '"edges"' in content:
        try:
            # Find the first { before "version" or "nodes"
            markers = ['"version"', '"diagram_metadata"', '"nodes"']
            first_marker_pos = min([content.find(m) for m in markers if content.find(m) != -1] or [len(content)])
            start_brace = content.rfind('{', 0, first_marker_pos)
            if start_brace != -1:
                # Find the last } after the last edge/node
                last_brace = content.rfind('}')
                if last_brace > start_brace:
                    candidate = content[start_brace:last_brace+1]
                    try:
                        return json.loads(clean_json_str(candidate))
                    except json.JSONDecodeError:
                        pass
        except:
            pass

    # If all fails, raise the original error or return empty
    raise json.JSONDecodeError("Could not extract valid JSON from content", content, 0)
