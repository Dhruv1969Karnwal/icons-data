import json
from mermaid.utils.json_helper import robust_json_loads

def test_robust_parsing():
    print("🧪 Starting Robust JSON Parsing Tests...")

    # Test Case 1: Standard JSON
    print("\n1. Standard JSON...")
    obj = {"test": "data"}
    res = robust_json_loads(json.dumps(obj))
    assert res == obj, f"Expected {obj}, got {res}"
    print("✅ Passed")

    # Test Case 2: Markdown JSON
    print("\n2. Markdown JSON block...")
    content = "Here is the result:\n```json\n{\"foo\": \"bar\"}\n```\nHope this helps!"
    res = robust_json_loads(content)
    assert res == {"foo": "bar"}
    print("✅ Passed")

    # Test Case 3: Extra Data (Concatenated objects)
    print("\n3. Extra Data (Concatenated objects)...")
    content = "{\"first\": 1}{\"second\": 2}"
    res = robust_json_loads(content)
    assert res == {"first": 1}
    print("✅ Passed")

    # Test Case 4: Deep preamble and think block
    print("\n4. Deep preamble and think block...")
    content = """<think>
    I should generate a JSON object.
    </think>
    After thinking, here it is:
    
    {
        "result": "success",
        "nested": {
            "key": "value"
        }
    }
    
    Goodbye!"""
    res = robust_json_loads(content)
    assert res == {"result": "success", "nested": {"key": "value"}}
    print("✅ Passed")

    # Test Case 5: Literal ... placeholder (common error from LLM)
    # Note: robust_json_loads doesn't explicitly fix ... yet, but let's see if it handles the start/end well
    # Actually, let's see if we can find the JSON even if it's broken.
    # If the JSON is truly broken with ..., robust_json_loads might still fail which is good (fail fast).

    print("\n🎉 All core robust parsing tests passed!")

if __name__ == "__main__":
    test_robust_parsing()
