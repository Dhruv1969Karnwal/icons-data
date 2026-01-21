import requests
import json
import time

def test_connectivity():
    url = "https://backend.v3.codemateai.dev/v2/chat/completions"
    headers = {
        "Authorization": "Bearer ba0981d9-4fb5-4974-9dae-0c878330c22a",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/web_chat",
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": 0.3
    }
    
    print(f"Testing connectivity to: {url}")
    print(f"Using API Key: {headers['Authorization'][:10]}...")
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        duration = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Duration: {duration:.2f}s")
        if response.status_code == 200:
            print("Response:", response.json()['choices'][0]['message']['content'])
        else:
            print("Error Response:", response.text)
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 20 seconds.")
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")

if __name__ == "__main__":
    test_connectivity()
