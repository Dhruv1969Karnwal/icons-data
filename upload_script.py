import json
import requests
from collections import defaultdict

with open('output/icons_rag.json', 'r') as f:
    icons = json.load(f)

# ✅ providers to keep
ALLOWED_PROVIDERS = {
    "Amazon Web Services",
    "Google Cloud Platform",
    "Infrastructure",
    "Microsoft Azure",
    "Technology",
}

# 1. Group icons by provider (filtered)
provider_map = defaultdict(list)

for icon in icons:
    provider = icon.get("provider")
    if provider in ALLOWED_PROVIDERS:
        provider_map[provider].append(icon)

# 2. Get set of providers and print them
providers = set(provider_map.keys())
print(f"Found {len(providers)} providers:")
for p in sorted(providers):
    print("-", p)

# 3. Take top 50 icons from each provider
filtered_icons = []
for provider, items in provider_map.items():
    filtered_icons.extend(items[:40])

print(f"\nTotal icons selected for upload: {len(filtered_icons)}")

# 4. Upload
response = requests.post(
    "http://localhost:8001/api/rag/upload",
    json={"icons": filtered_icons}
)

print(response.status_code)
print(response.json())
