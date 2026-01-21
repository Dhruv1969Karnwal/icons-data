import requests
import numpy as np
import json
from typing import List, Dict
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, SparseVectorParams, SparseVector, Prefetch, FusionQuery, Fusion
import hashlib
import asyncio
import os
from pathlib import Path

# ==================== EMBEDDING FUNCTION ====================
def get_embedding_normalized(text: str) -> np.ndarray:
    """Get normalized embedding from llama.cpp"""
    print(f"DEBUG: Requesting embedding for text (len: {len(text)})...")
    try:
        response = requests.post(
            "http://localhost:8000/embeddings",
            json={"input": text},
            # timeout=10
        )
        response.raise_for_status()
        data = response.json()
        print(f"DEBUG: Received response from embedding server")
    except Exception as e:
        print(f"ERROR: Embedding request failed: {e}")
        raise
    
    # Parse response
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        token_embeddings = np.array([item["embedding"] for item in data])
    elif isinstance(data, dict) and "data" in data:
        token_embeddings = np.array([item["embedding"] for item in data["data"]])
    else:
        print(f"ERROR: Unknown response format: {data}")
        raise ValueError("Unknown response format")
    
    print(f"DEBUG: Parsed embeddings shape: {token_embeddings.shape}")
    
    # Handle 3D embeddings (Qwen returns batch x layers x dims)
    if token_embeddings.ndim == 3:
        token_embeddings = token_embeddings.reshape(-1, token_embeddings.shape[-1])
    
    # Pool: take mean across all tokens
    pooled = np.mean(token_embeddings, axis=0)
    
    # Normalize
    norm_magnitude = np.linalg.norm(pooled)
    normalized = pooled / norm_magnitude
    
    return normalized.tolist()

def get_sparse_embedding(text: str) -> Dict[int, float]:
    """
    Generate a simple sparse embedding (BM25-like/TF-IDF)
    In a real scenario, use a proper sparse model like SPLADE.
    For local testing, we'll use a simple term-frequency map with hashing.
    """
    import re
    from collections import Counter
    
    # Tokenize and clean
    words = re.findall(r'\w+', text.lower())
    counts = Counter(words)
    total = sum(counts.values())
    
    sparse_vec = {}
    for word, count in counts.items():
        # Simple hashing for the index
        index = int(hashlib.md5(word.encode()).hexdigest(), 16) % (2**31 - 1)
        # TF-based weight
        weight = count / total
        sparse_vec[index] = float(weight)
        
    return sparse_vec

# ==================== DOCUMENT PREPARATION ====================
def prepare_search_document(icon: Dict) -> str:
    """Create searchable document from icon metadata"""
    display_name = icon.get("display_name", "")
    provider = icon.get("provider", "")
    category = icon.get("tags", "[]")
    technical_intent = icon.get("technical_intent", "")
    semantic_profile = icon.get("semantic_profile", "")
    aliases = icon.get("aliases", "[]")
    
    # Parse tags if it's a JSON string
    if isinstance(category, str):
        try:
            category = json.loads(category)
        except:
            category = []
    category_str = ", ".join(category) if isinstance(category, list) else str(category)
    
    # Parse aliases if it's a JSON string
    if isinstance(aliases, str):
        try:
            aliases = json.loads(aliases)
        except:
            aliases = []
    aliases_str = ", ".join(aliases) if isinstance(aliases, list) else str(aliases)
    
    # Precise format: {display_name} by {provider}. Category: {tags}. Intent: {technical_intent}. Profile: {semantic_profile}. Aliases: {aliases}.
    search_doc = f"{display_name} by {provider}. Category: [{category_str}]. Intent: {technical_intent}. Profile: {semantic_profile}. Aliases: {aliases_str}."
    return search_doc

# ==================== QDRANT CLIENT - LOCAL ====================
class IconRAGPipeline:
    def __init__(self, qdrant_client: AsyncQdrantClient, collection_name: str = "icons", backup_file: str = "icons_backup.json"):
        """
        Initialize with your local Qdrant client
        
        Storage Structure:
        ===================
        COLLECTION: "icons" (one collection for all icons)
        └─ Each icon becomes ONE POINT:
           ├─ Point ID: hash of icon["id"]
           ├─ Vector: 2048-dim embedding (from search_document)
           └─ Payload: All icon metadata (not embedded)
        
        Storage Breakdown:
        - Per icon: ~8KB vector + ~3KB payload = ~11KB
        - 1000 icons: ~11MB
        - 10,000 icons: ~110MB
        - 100,000 icons: ~1.1GB
        """
        self.client = qdrant_client
        self.collection_name = collection_name
        self.vector_size = 2048  # Qwen embedding dimension
        self.backup_file = backup_file
        
    async def create_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            # Check if collection exists
            await self.client.get_collection(self.collection_name)
            print(f"✓ Collection '{self.collection_name}' already exists")
        except:
            # Create collection with both Dense and Sparse support
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "text": SparseVectorParams(
                        index=None
                    )
                }
            )
            print(f"✓ Created collection '{self.collection_name}' with named dense and sparse support")
    
    async def index_icons(self, icons: List[Dict]) -> int:
        """
        Index icons into Qdrant (ONE POINT PER ICON).
        
        STORAGE STRUCTURE:
        ==================
        Storage Method: Per-Icon-Per-Point
        - Each icon → 1 Point in collection
        - Point ID: hash(icon["id"])
        - Vector: 2048 dims (from search_document only)
        - Payload: All 20+ fields stored as metadata
        
        NOT stored per collection level, stored per individual point.
        Each point has its own vector + metadata.
        """
        points = []
        print(f"DEBUG: Preparing to index {len(icons)} icons...")
        for idx, icon in enumerate(icons):
            # ===== STEP 1: Generate EMBEDDING from selected fields only =====
            search_doc = prepare_search_document(icon)
            
            # Add instruction for better embeddings (Instruction-Aware Indexing)
            indexing_instruction = "Represent this technical infrastructure component for retrieval in architecture diagrams."
            full_text = f"{indexing_instruction} {search_doc}"
            
            # THIS generates the 2048-dim vector
            print(f"  [{idx+1}/{len(icons)}] Embedding icon: {icon.get('display_name', 'Unknown')}")
            dense_embedding = get_embedding_normalized(full_text)
            sparse_dict = get_sparse_embedding(search_doc)
            sparse_embedding = SparseVector(
                indices=list(sparse_dict.keys()),
                values=list(sparse_dict.values())
            )
            
            # ===== STEP 2: Create POINT (icon) with vectors + all metadata =====
            point_id = int(hashlib.md5(icon["id"].encode()).hexdigest(), 16) % (10 ** 8)
            
            point = PointStruct(
                id=point_id,
                vector={
                    "dense": dense_embedding,
                    "text": sparse_embedding
                },
                payload={
                    # All icon fields stored as metadata
                    "id": icon.get("id", ""),
                    "slug": icon.get("slug", ""),
                    "display_name": icon.get("display_name", ""),
                    "provider": icon.get("provider", ""),
                    "url": icon.get("url", ""),
                    "iconify_id": icon.get("iconify_id", ""),
                    "semantic_profile": icon.get("semantic_profile", ""),
                    "aliases": icon.get("aliases", ""),
                    "technical_intent": icon.get("technical_intent", ""),
                    "description": icon.get("description", ""),
                    "tags": icon.get("tags", ""),
                    "shape_type": icon.get("shape_type", ""),
                    "default_width": icon.get("default_width", ""),
                    "is_container": icon.get("is_container", ""),
                    "icon_position": icon.get("icon_position", ""),
                    "color_theme": icon.get("color_theme", ""),
                    "popularity": icon.get("popularity", ""),
                    "last_scraped": icon.get("last_scraped", ""),
                     # Helper field
                    "search_document": search_doc
                }
            )
            points.append(point)
            
            if (idx + 1) % 10 == 0:
                print(f"  Processed {idx + 1} icons...")
        
        # ===== STEP 3: Upload to Qdrant in batches =====
        batch_size = 100
        print(f"DEBUG: Upserting {len(points)} points to Qdrant in batches...")
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            await self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            print(f"  Upserted batch {i//batch_size + 1}")
        
        print(f"✓ Indexed {len(points)} icons into collection '{self.collection_name}'")
        
        # Automatically save to disk after indexing
        await self.save_to_disk()
        
        return len(points)
    
    async def save_to_disk(self, filename: str = None):
        """Export all points (vectors + payloads) from Qdrant to a JSON file"""
        fname = filename or self.backup_file
        print(f"DEBUG: Saving collection '{self.collection_name}' to {fname}...")
        
        all_points = []
        offset = None
        while True:
            response = await self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                with_vectors=True,
                with_payload=True,
                offset=offset
            )
            points, next_page_offset = response
            for p in points:
                # Convert SparseVector to dict for JSON serialization
                vectors = p.vector
                if isinstance(vectors, dict):
                    if "text" in vectors and hasattr(vectors["text"], "indices"):
                        vectors["text"] = {
                            "indices": vectors["text"].indices,
                            "values": vectors["text"].values
                        }
                
                all_points.append({
                    "id": p.id,
                    "vector": vectors,
                    "payload": p.payload
                })
            
            offset = next_page_offset
            if offset is None:
                break
        
        with open(fname, "w") as f:
            json.dump(all_points, f)
        print(f"✓ Saved {len(all_points)} icons to {fname}")

    async def load_from_disk(self, filename: str = None) -> int:
        """Import points from a JSON file directly into Qdrant"""
        fname = filename or self.backup_file
        if not os.path.exists(fname):
            print(f"WARNING: Backup file {fname} not found. Skipping restore.")
            return 0
        
        print(f"DEBUG: Loading icons from {fname}...")
        with open(fname, "r") as f:
            data = json.load(f)
        
        points = []
        for item in data:
            # Reconstruct SparseVector if needed
            vectors = item["vector"]
            if isinstance(vectors, dict) and "text" in vectors and isinstance(vectors["text"], dict):
                vectors["text"] = SparseVector(
                    indices=vectors["text"]["indices"],
                    values=vectors["text"]["values"]
                )
            
            points.append(PointStruct(
                id=item["id"],
                vector=vectors,
                payload=item["payload"]
            )
            )
        
        # Batch upsert
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            await self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
        
        print(f"✓ Restored {len(points)} icons from {fname} into '{self.collection_name}'")
        return len(points)
    
    async def search_icons(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for icons using native hybrid search (Dense + Sparse) + RRF"""
        
        # 1. Generate Query Embeddings
        # Semantic (Dense)
        search_instruction = "Retrieve cloud infrastructure components relevant to architecture diagrams."
        full_query = f"{search_instruction} {query}"
        dense_query = get_embedding_normalized(full_query)
        
        # Keyword (Sparse)
        sparse_dict = get_sparse_embedding(query)
        sparse_query = SparseVector(
            indices=list(sparse_dict.keys()),
            values=list(sparse_dict.values())
        )
        
        print(f"DEBUG: Performing hybrid search for: '{query}'")
        
        # 2. Hybrid Search using RRF
        try:
            query_response = await self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    Prefetch(
                        query=dense_query,
                        using="dense",
                        limit=20
                    ),
                    Prefetch(
                        query=sparse_query,
                        using="text",
                        limit=20
                    )
                ],
                query=FusionQuery(fusion=Fusion.RRF),
                limit=top_k
            )
            
            results = []
            for hit in query_response.points:
                results.append({
                    **hit.payload,
                    "score": float(hit.score) if hit.score else 0.0,
                    "search_type": "hybrid"
                })
            
            return results
            
        except Exception as e:
            print(f"ERROR: Hybrid search failed: {e}. Falling back to dense search.")
            # Fallback to dense only if hybrid fails (e.g. older Qdrant version)
            query_response = await self.client.query_points(
                collection_name=self.collection_name,
                query=dense_query,
                using="dense",
                limit=top_k
            )
            return [ {**hit.payload, "score": hit.score, "search_type": "dense"} for hit in query_response.points ]
    
    async def get_collection_stats(self) -> Dict:
        """Get collection statistics"""
        try:
            collection_info = await self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "vector_size": self.vector_size,
                "points_count": collection_info.points_count,
                "status": collection_info.status
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def delete_collection(self):
        """Delete collection"""
        try:
            await self.client.delete_collection(self.collection_name)
            print(f"✓ Deleted collection '{self.collection_name}'")
        except Exception as e:
            print(f"✗ Error deleting collection: {e}")

# ==================== FASTAPI SERVER ====================
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Icon RAG API (Local Qdrant)")

rag = None

class IconData(BaseModel):
    icons: List[Dict]

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

@app.post("/api/rag/upload")
async def upload_icons(data: IconData):
    """
    Upload icons to local Qdrant index.
    
    POST /api/rag/upload
    {
        "icons": [
            {
                "id": "uuid",
                "slug": "essentials-add",
                "display_name": "Add",
                ...
            }
        ]
    }
    
    Storage: Each icon becomes ONE point in the collection with:
    - Vector: 2048-dim embedding
    - Metadata: All icon fields stored in payload
    """
    try:
        print(f"DEBUG: Received upload request for {len(data.icons)} icons")
        if not rag:
            print("ERROR: RAG pipeline not initialized")
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
        
        await rag.create_collection()
        print("DEBUG: Collection checked/created. Starting indexing...")
        count = await rag.index_icons(data.icons)
        
        return {
            "status": "success",
            "message": f"Indexed {count} icons into local Qdrant",
            "count": count
        }
    except Exception as e:
        import traceback
        print(f"ERROR in upload_icons: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/rag/search")
async def search_icons(q: str, top_k: int = 5):
    """
    Search icons by query.
    
    GET /api/rag/search?q=object%20storage&top_k=5
    """
    try:
        if not rag:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
        
        if not q or len(q.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        results = await rag.search_icons(q, top_k=top_k)
        with open("rag_search_results.json", "w") as f:
            json.dump(results, f)
        return {
            "status": "success",
            "query": q,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/rag/stats")
async def get_stats():
    """Get collection statistics"""
    try:
        if not rag:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
        
        stats = await rag.get_collection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/rag/backup")
async def backup_rag():
    """Manually trigger a backup to file"""
    try:
        if not rag:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
        await rag.save_to_disk()
        return {"status": "success", "message": f"Backup saved to {rag.backup_file}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/rag/restore")
async def restore_rag():
    """Manually trigger a restore from file"""
    try:
        if not rag:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
        await rag.create_collection()
        count = await rag.load_from_disk()
        return {"status": "success", "message": f"Restored {count} icons from {rag.backup_file}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.on_event("startup")
async def startup():
    """Initialize RAG pipeline on startup"""
    global rag
    
    # Use persistent storage instead of :memory:
    storage_path = "./qdrant_storage"
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)
        
    qdrant_client = AsyncQdrantClient(path=storage_path)
    
    rag = IconRAGPipeline(
        qdrant_client=qdrant_client,
        collection_name="icons_collection" # Standardized name
    )
    
    # Automatic Restore Check
    try:
        await rag.create_collection()
        collection_info = await qdrant_client.get_collection(rag.collection_name)
        if collection_info.points_count == 0:
            print("DEBUG: Collection is empty. Checking for backup file...")
            if os.path.exists(rag.backup_file):
                count = await rag.load_from_disk()
                print(f"✓ Automatically restored {count} icons from backup")
            else:
                print("DEBUG: No backup file found. Ready for new indexing.")
        else:
            print(f"✓ Collection contains {collection_info.points_count} points. Ready.")
    except Exception as e:
        print(f"WARNING: Startup check failed: {e}")
        # Collection might not exist yet, which is fine for first run
    print("✓ RAG pipeline initialized with local Qdrant")

# ==================== USAGE EXAMPLE ====================
if __name__ == "__main__":
    import uvicorn
    
    # Run with: uvicorn script_name:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8001)