#!/usr/bin/env python3
import json
import asyncio
import os
import sys
import time
from typing import List, Dict
from llm_service_sync import aclassify_icon

INPUT_FILE = "output/icons_rag.json"
SUCCESS_FILE = "output/enriched_icons.json"
ERROR_FILE = "output/error_icons.json"
BATCH_SIZE = 5

async def enrich_batch(batch: List[Dict]) -> List[Dict]:
    """Process a batch of icons concurrently"""
    tasks = []
    print(f"   [Batch] Starting concurrent processing for {len(batch)} icons...")
    for icon in batch:
        slug = icon.get('slug', 'unknown')
        print(f"      - Queueing enrichment for: {slug}")
        tasks.append(aclassify_icon(
            icon.get('provider', ''),
            slug, # Using slug as title for better context if title is missing
            icon.get('display_name', '')
        ))
    
    start = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time.time() - start
    print(f"   [Batch] All tasks in this batch finished in {elapsed:.2f}s")
    
    processed_results = []
    for icon, result in zip(batch, results):
        if isinstance(result, Exception):
            processed_results.append({"icon": icon, "error": str(result), "status": "failed"})
        elif "error" in result:
            processed_results.append({"icon": icon, "error": result["error"], "status": "failed"})
        else:
            # Merge original icon data with LLM results
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

    # For testing, you might want to slice the icons list
    # icons = icons[:10] 

    print(f"Total icons to process: {len(icons)}")
    
    success_icons = []
    error_icons = []
    
    # Optional: Resume from existing files if needed
    # (Simplified here to always overwrite or start fresh)

    for i in range(0, len(icons), BATCH_SIZE):
        batch = icons[i:i + BATCH_SIZE]
        print(f"Processing batch {i//BATCH_SIZE + 1}/{(len(icons) + BATCH_SIZE - 1)//BATCH_SIZE}...")
        
        results = await enrich_batch(batch)
        
        for res in results:
            if res["status"] == "success":
                success_icons.append(res["icon"])
            else:
                # Add original icon and error info to error list
                failed_item = res["icon"].copy()
                failed_item["enrichment_error"] = res["error"]
                error_icons.append(failed_item)

        # Write progress periodically
        with open(SUCCESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(success_icons, f, indent=2)
        
        with open(ERROR_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_icons, f, indent=2)

    print("\nProcessing complete!")
    print(f"Successfully enriched: {len(success_icons)}")
    print(f"Failed: {len(error_icons)}")
    print(f"Results saved to {SUCCESS_FILE} and {ERROR_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
