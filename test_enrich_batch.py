#!/usr/bin/env python3
import json
import asyncio
import os
import sys
from typing import List, Dict
from llm_service_sync import aclassify_icon

INPUT_FILE = "output/icons_rag.json"
SUCCESS_FILE = "output/test_enriched_icons.json"
ERROR_FILE = "output/test_error_icons.json"
BATCH_SIZE = 2 # Small batch for testing

async def enrich_batch(batch: List[Dict]) -> List[Dict]:
    """Process a batch of icons concurrently"""
    tasks = []
    for icon in batch:
        tasks.append(aclassify_icon(
            icon.get('provider', ''),
            icon.get('slug', ''),
            icon.get('display_name', '')
        ))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    processed_results = []
    for icon, result in zip(batch, results):
        if isinstance(result, Exception):
            processed_results.append({"icon": icon, "error": str(result), "status": "failed"})
        elif "error" in result:
            processed_results.append({"icon": icon, "error": result["error"], "status": "failed"})
        else:
            enriched_icon = icon.copy()
            enriched_icon.update(result)
            processed_results.append({"icon": enriched_icon, "status": "success"})
            
    return processed_results

async def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file {INPUT_FILE} not found.")
        return

    print(f"Reading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        icons = json.load(f)

    # PROCESS ONLY 2 ICONS FOR TESTING
    icons = icons[:2] 

    print(f"Total icons to process: {len(icons)}")
    
    success_icons = []
    error_icons = []
    
    for i in range(0, len(icons), BATCH_SIZE):
        batch = icons[i:i + BATCH_SIZE]
        print(f"Processing test batch {i//BATCH_SIZE + 1}...")
        
        results = await enrich_batch(batch)
        
        for res in results:
            if res["status"] == "success":
                success_icons.append(res["icon"])
            else:
                failed_item = res["icon"].copy()
                failed_item["enrichment_error"] = res["error"]
                error_icons.append(failed_item)

        with open(SUCCESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(success_icons, f, indent=2)
        
        with open(ERROR_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_icons, f, indent=2)

    print("\nTest processing complete!")
    print(f"Successfully enriched: {len(success_icons)}")
    print(f"Failed: {len(error_icons)}")

if __name__ == "__main__":
    asyncio.run(main())
