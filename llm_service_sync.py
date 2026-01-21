#!/usr/bin/env python3
"""
LLM Enrichment HTTP Service - Enhanced Universal Version
Implements senior developer recommendations for production-grade icon classification
"""

from flask import Flask, request, jsonify
import json
import re
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
from litellm import completion, acompletion
import time

app = Flask(__name__)

# Enhanced tool definition with is_container and expanded categories
TOOLS = [{
    "type": "function",
    "function": {
        "name": "classify_icon",
        "description": "Enrich architecture icon metadata for universal RAG-based diagramming",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": [
                        "compute", "storage", "database", "network", "security",
                        "queue", "devops", "iot", "api", "monitoring",
                        "frontend", "language", "framework", "os", "saas", "branding", "general"
                    ],
                    "description": "Primary architectural category"
                },
                "shape_type": {
                    "type": "string",
                    "enum": [
                        "cylinder", "sql_table", "queue", "cloud", "rectangle",
                        "package", "hexagon", "circle", "image"
                    ],
                    "description": "D2 shape type for diagram rendering"
                },
                "is_container": {
                    "type": "boolean",
                    "description": "True if this entity groups other components (VPC, Cluster, Namespace, etc.)"
                },
                "aliases": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Common abbreviations and alternative names"
                },
                "technical_intent": {
                    "type": "string",
                    "description": "Concise architectural purpose (8-12 words max)"
                },
                "semantic_profile": {
                    "type": "string",
                    "description": "Detailed technical description for RAG embeddings (20-40 words)"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Relevant technical tags for filtering"
                },
                "brand_color": {
                    "type": "string",
                    "description": "Official HEX color code (e.g., #FF9900 for AWS)"
                }
            },
            "required": [
                "category", "shape_type", "is_container", "aliases",
                "technical_intent", "semantic_profile", "tags", "brand_color"
            ]
        }
    }
}]

# Enhanced system prompt with clear RAG guidance
SYSTEM_PROMPT = """You are a specialized architecture icon classifier for a RAG-based diagramming system.

**Shape Mapping Rules:**
- cylinder: Storage services, object stores, blob storage
- sql_table: Relational databases (RDS, PostgreSQL, MySQL)
- queue: Message queues, event streams (SQS, Kafka, Service Bus)
- cloud: Networks, VPCs, virtual networks, CDNs
- rectangle: Compute instances, VMs, containers, serverless functions
- package: DevOps tools, CI/CD, deployment services
- hexagon: APIs, gateways, management services
- circle: Monitoring, logging, metrics, observability
- image: General/uncategorized icons

**Container Detection:**
Set is_container=true for entities that group other components:
- VPCs, VNets, Subnets, Security Groups
- Kubernetes Clusters, Namespaces, Pods
- Resource Groups, Availability Zones
- Load Balancers (when acting as entry points)

**Field Generation Guidelines:**
1. technical_intent: 8-12 words describing architectural role
   Example: "Managed relational database for transactional workloads with automatic backups"

2. semantic_profile: 20-40 words for RAG embeddings, focus on:
   - What problem it solves
   - Key capabilities
   - Common use cases
   Example: "Amazon RDS provides managed relational database hosting with automated backups, patching, and scaling. Supports MySQL, PostgreSQL, Oracle, and SQL Server. Used for transactional applications requiring ACID compliance and traditional SQL queries."

3. aliases: Include abbreviations, alternative names, common misspellings
   Example: For "Simple Storage Service" → ["S3", "object storage", "blob storage"]

4. tags: Technical keywords for filtering (3-7 tags)
   Example: ["managed", "serverless", "storage", "aws"]

5. brand_color: Use official brand colors. If unknown, infer from provider:
   - AWS: #FF9900
   - Azure: #0078D4
   - GCP: #4285F4
   - Generic tech: #6366F1
   - Open source: #10B981

Respond ONLY with the classify_icon function call."""

# Official brand colors (comprehensive)
PROVIDER_COLORS = {
    # Cloud Providers
    "AWS": "#FF9900",
    "AZURE": "#0078D4",
    "GCP": "#4285F4",
    "DIGITALOCEAN": "#0080FF",
    "ORACLE": "#F80000",
    "IBM": "#054ADA",
    "ALIBABA": "#FF6A00",
    
    # Development Tools
    "DEV": "#6366F1",
    "GITHUB": "#181717",
    "GITLAB": "#FC6D26",
    "DOCKER": "#2496ED",
    "KUBERNETES": "#326CE5",
    
    # Categories
    "INFRA": "#10B981",
    "TECH": "#8B5CF6",
    "SOCIAL": "#EC4899",
    "ESSENTIALS": "#64748B",
    "EMOTIONS": "#F59E0B",
    
    # Popular Technologies
    "REACT": "#61DAFB",
    "ANGULAR": "#DD0031",
    "VUE": "#4FC08D",
    "PYTHON": "#3776AB",
    "JAVASCRIPT": "#F7DF1E",
    "TYPESCRIPT": "#3178C6",
    "JAVA": "#007396",
    "GO": "#00ADD8",
    "RUST": "#000000",
    "REDIS": "#DC382D",
    "MONGODB": "#47A248",
    "POSTGRESQL": "#4169E1",
    "MYSQL": "#4479A1",
}

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=10)


def classify_icon(provider: str, title: str, display_name: str) -> dict:
    """
    Classify icon using LLM with enhanced prompting
    
    Args:
        provider: Source folder/provider (AWS, GCP, Dev, etc.)
        title: Raw service name from scraper
        display_name: Cleaned display name
        
    Returns:
        dict: Enriched classification data
    """
    user_prompt = f"""Analyze this technology asset for architecture diagramming:

**Source Folder:** {provider}
**Service Name:** {title}
**Display Label:** {display_name}

Determine:
1. Most accurate category and D2 shape type
2. Whether it acts as a container for other components
3. Technical intent and detailed semantic profile for RAG search
4. Common aliases and relevant tags
5. Official brand color

Call classify_icon with complete metadata."""

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        # Use synchronous completion with strict tool calling
        response = completion(
            base_url="https://backend.v3.codemateai.dev/v2",
            api_key="988fe7dd-5a67-4c93-a435-abdb03bd383c",
            model="openai/web_chat",
            messages=messages,
            tools=TOOLS,
            tool_choice={"type": "function", "function": {"name": "classify_icon"}},
            temperature=0.1,  # Low temperature for consistency
        )

        # Debug logging to stderr (won't corrupt JSON output)
        print(f"[DEBUG] Classified: {title}", file=sys.stderr)

        if response.choices and response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            args_str = tool_call.function.arguments
            
            # Robust JSON extraction (handles LLM wrapper text)
            json_match = re.search(r'\{[\s\S]*\}', args_str)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(args_str)
            
            # Validate and set defaults
            if not result.get("brand_color") or result["brand_color"] == "":
                result["brand_color"] = PROVIDER_COLORS.get(
                    provider.upper(),
                    "#6B7280"  # Default gray
                )
            
            # Ensure all required fields exist
            result.setdefault("is_container", False)
            result.setdefault("aliases", [])
            result.setdefault("tags", [provider.lower()])
            
            return result
        
        raise ValueError("No tool calls in LLM response")
        
    except Exception as e:
        print(f"[ERROR] LLM failed for {title}: {e}", file=sys.stderr)
        return {
            "category": "",
            "shape_type": "",
            "is_container": False,
            "aliases": [],
            "technical_intent": "",
            "semantic_profile": "",
            "tags": [],
            "brand_color": ""
        }


async def aclassify_icon(provider: str, title: str, display_name: str) -> dict:
    """
    Classify icon using LLM asynchronously
    
    Args:
        provider: Source folder/provider (AWS, GCP, Dev, etc.)
        title: Raw service name from scraper
        display_name: Cleaned display name
        
    Returns:
        dict: Enriched classification data
    """
    user_prompt = f"""Analyze this technology asset for architecture diagramming:

**Source Folder:** {provider}
**Service Name:** {title}
**Display Label:** {display_name}

Determine:
1. Most accurate category and D2 shape type
2. Whether it acts as a container for other components
3. Technical intent and detailed semantic profile for RAG search
4. Common aliases and relevant tags
5. Official brand color

Call classify_icon with complete metadata."""

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        # Use asynchronous completion
        response = await acompletion(
            base_url="https://backend.v3.codemateai.dev/v2",
            api_key="988fe7dd-5a67-4c93-a435-abdb03bd383c",
            model="openai/web_chat",
            messages=messages,
            tools=TOOLS,
            tool_choice={"type": "function", "function": {"name": "classify_icon"}},
            temperature=0.1,
        )

        print(f"[DEBUG] [ASYNC] Classified: {title}", file=sys.stderr)

        if response.choices and response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            args_str = tool_call.function.arguments
            
            json_match = re.search(r'\{[\s\S]*\}', args_str)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(args_str)
            
            if not result.get("brand_color"):
                result["brand_color"] = PROVIDER_COLORS.get(
                    provider.upper(),
                    "#6B7280"
                )
            
            result.setdefault("is_container", False)
            result.setdefault("aliases", [])
            result.setdefault("tags", [provider.lower()])
            
            return result
        
        raise ValueError("No tool calls in LLM response")
        
    except Exception as e:
        print(f"[ERROR] [ASYNC] LLM failed for {title}: {e}", file=sys.stderr)
        return {
            "error": str(e),
            "category": "",
            "shape_type": "",
            "is_container": False,
            "aliases": [],
            "technical_intent": "",
            "semantic_profile": "",
            "tags": [],
            "brand_color": ""
        }


@app.route('/classify', methods=['POST'])
def classify_endpoint():
    """HTTP endpoint for icon classification"""
    try:
        data = request.json
        provider = data.get('provider', '')
        title = data.get('title', '')
        display_name = data.get('display_name', '')
        
        if not all([provider, title, display_name]):
            return jsonify({"error": "Missing required fields: provider, title, display_name"}), 400
        
        start_time = time.time()
        result = classify_icon(provider, title, display_name)
        elapsed = time.time() - start_time
        
        # Add performance metadata
        result['_processing_time_ms'] = round(elapsed * 1000, 2)
        
        return jsonify(result)
            
    except Exception as e:
        print(f"[ERROR] classify endpoint: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500


@app.route('/batch', methods=['POST'])
def batch_classify_endpoint():
    """
    Batch classification endpoint for parallel processing
    
    Expected payload:
    {
        "icons": [
            {"provider": "AWS", "title": "ec2", "display_name": "EC2"},
            {"provider": "GCP", "title": "gcs", "display_name": "Cloud Storage"}
        ]
    }
    """
    try:
        data = request.json
        icons = data.get('icons', [])
        
        if not icons or not isinstance(icons, list):
            return jsonify({"error": "Expected 'icons' array in request"}), 400
        
        start_time = time.time()
        
        # Process in parallel using thread pool
        def process_icon(icon_data):
            try:
                return classify_icon(
                    icon_data.get('provider', ''),
                    icon_data.get('title', ''),
                    icon_data.get('display_name', '')
                )
            except Exception as e:
                print(f"[ERROR] Batch item failed: {e}", file=sys.stderr)
                return {"error": str(e)}
        
        results = list(executor.map(process_icon, icons))
        elapsed = time.time() - start_time
        
        return jsonify({
            "results": results,
            "total": len(results),
            "processing_time_ms": round(elapsed * 1000, 2),
            "avg_time_per_icon_ms": round((elapsed * 1000) / len(results), 2)
        })
            
    except Exception as e:
        print(f"[ERROR] batch endpoint: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint with service info"""
    return jsonify({
        "status": "ok",
        "service": "LLM Enrichment API - Enhanced Universal Version",
        "version": "2.0",
        "features": [
            "Enhanced category detection",
            "Container identification",
            "RAG semantic profiles",
            "Batch processing support",
            "Brand color management"
        ]
    })


if __name__ == '__main__':
    print("=" * 70)
    print("🚀 LLM Enrichment Service - Enhanced Universal Version")
    print("=" * 70)
    print("📍 Endpoints:")
    print("   GET  /health        - Health check with service info")
    print("   POST /classify      - Single icon classification")
    print("   POST /batch         - Batch icon classification (parallel)")
    print("")
    print("🔧 Features:")
    print("   ✓ Expanded categories (17 types)")
    print("   ✓ Container detection (VPC, Cluster, etc.)")
    print("   ✓ RAG semantic profiles for embeddings")
    print("   ✓ Official brand color management")
    print("   ✓ Parallel batch processing")
    print("")
    print("🌐 Server: http://localhost:5000")
    print("=" * 70)
    print("")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)