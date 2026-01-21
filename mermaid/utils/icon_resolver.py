import json
import requests
import random
import os
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
from mermaid.config import QDRANT_API_BASE, DEFAULT_ICON

class IconResolver:
    """Resolves technology names to Iconify icon URLs with caching."""
    
    def __init__(self):
        self.cache = {}
        self.static_icons = []
        self._load_static_index()

    def _load_static_index(self):
        """Load static icon index from JSON file."""
        paths_to_try = [
            "icons_rag.json",
            "output/icons_rag.json",
            "c:/Users/Dhruv/Desktop/CodeMate.AI/extra_research/terrastruct-icons/icons_rag.json"
        ]
        for path in paths_to_try:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.static_icons = json.load(f)
                    print(f"   📂 [IconResolver] Loaded {len(self.static_icons)} icons from {path}")
                    return
                except Exception as e:
                    print(f"   ⚠️ [IconResolver] Failed to load {path}: {e}")
        print("   ❌ [IconResolver] Could not find any static icon index file.")

    @lru_cache(maxsize=500)
    def search_icon(self, technology: str) -> Tuple[Optional[str], Optional[str]]:
        """Search for an icon using local static index (primary), then fallback to random static icon."""
        print(f"\n🔍 [IconResolver] Searching icon for technology: '{technology}'")
        
        # 0. Try local static index first
        # if self.static_icons:
            # print(f"   📡 [IconResolver] Trying local static lookup for '{technology}'...")
            # tech_lower = technology.lower()
            # for icon in self.static_icons:
            #     # Match by slug, display_name or title
            #     if tech_lower in icon.get("slug", "").lower() or \
            #        tech_lower in icon.get("display_name", "").lower() or \
            #        tech_lower in icon.get("id", "").lower():
            #         icon_url = icon.get("url")
            #         shape_type = icon.get("shape_type", "image")
            #         print(f"   ✅ [IconResolver] Found icon in static index: {icon_url} (Shape: {shape_type})")
            #         return icon_url, shape_type
            
            # # If no direct match found in static list, use a random one as requested
            # print(f"   ⚠️ [IconResolver] No match for '{technology}' in static index. Using random fallback.")
            # random_icon = random.choice(self.static_icons)
            # icon_url = random_icon.get("url")
            # shape_type = random_icon.get("shape_type", "image")
            # print(f"   🎲 [IconResolver] Randomly selected: {icon_url} (Shape: {shape_type})")
            # return icon_url, shape_type

        # if True:
        #     return DEFAULT_ICON, "image"

        # 1. Fallback to Qdrant search (only if static icons weren't loaded)
        try:
            print(f"   📡 [IconResolver] Trying Qdrant search for '{technology}'...")
            qdrant_url = f"{QDRANT_API_BASE}/search"
            params = {"q": technology, "top_k": 1}
            # Increased timeout to 15s to allow for local embedding generation
            response = requests.get(qdrant_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    hit = results[0]
                    icon_url = hit.get("url")
                    shape_type = hit.get("shape_type")
                    if icon_url:
                        print(f"   ✅ [IconResolver] Found icon via Qdrant: {icon_url} (Shape: {shape_type})")
                        return icon_url, shape_type
            else:
                print(f"   ❌ [IconResolver] Qdrant search failed with status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ [IconResolver] Qdrant search exception: {type(e).__name__}: {e}")

        print(f"   ❌ [IconResolver] Using absolute default icon for '{technology}'")
        return DEFAULT_ICON, "image"
    
    def resolve_icons(self, nodes: List[Dict]) -> List[Dict]:
        """Resolve icon URLs for all nodes."""
        print(f"\n🎨 [IconResolver] Starting icon resolution for {len(nodes)} nodes")
        for idx, node in enumerate(nodes, 1):
            node_id = node.get("id", f"node_{idx}")
            print(f"\n   🔹 [IconResolver] Processing node {idx}/{len(nodes)}: '{node_id}'")
            if "technology" in node and not node.get("icon_url"):
                tech = node["technology"]
                print(f"      Technology: '{tech}'")
                icon_url, shape_type = self.search_icon(tech)
                node["icon_url"] = icon_url
                node["shape_type"] = shape_type
                print(f"      ✅ Resolved to: {icon_url} (Shape: {shape_type})")
            elif node.get("icon_url"):
                print(f"      ℹ️  Icon URL already exists: {node['icon_url']}")
            else:
                print(f"      ⚠️  No 'technology' field found, skipping icon resolution")
        print(f"\n✅ [IconResolver] Icon resolution complete!\n")
        return nodes
