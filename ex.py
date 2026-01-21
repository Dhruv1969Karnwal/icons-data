import requests
import numpy as np
import json

def get_embedding_normalized(text):
    """
    Get embeddings from llama.cpp, pool token-wise embeddings, and normalize
    """
    # Step 1: Request embeddings from llama.cpp
    response = requests.post(
        "http://localhost:8000/embeddings",
        json={"input": text}
    )
    
    data = response.json()
    
    print(f"Response type: {type(data)}")
    print(f"Response length: {len(data)}")
    if isinstance(data, list) and len(data) > 0:
        print(f"First item type: {type(data[0])}")
        if isinstance(data[0], dict):
            print(f"First item keys: {list(data[0].keys())}")
    
    # Step 2: Extract token embeddings
    # Response is a list where each item is a dict with embedding
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        # List of dicts, extract embedding from each
        if "embedding" in data[0]:
            token_embeddings = np.array([item["embedding"] for item in data])
        else:
            # Try other keys
            print(f"Available keys in first item: {list(data[0].keys())}")
            raise ValueError("No 'embedding' key found")
    elif isinstance(data, list):
        # Direct list of embeddings
        token_embeddings = np.array(data)
    elif isinstance(data, dict) and "data" in data:
        # OpenAI format with "data" key
        token_embeddings = np.array([item["embedding"] for item in data["data"]])
    else:
        # Try to find embedding in dict
        print("Response structure:", list(data.keys()) if isinstance(data, dict) else "Not a dict")
        raise ValueError("Unknown response format")
    
    print(f"Got {len(token_embeddings)} token embeddings")
    print(f"Token embeddings shape: {token_embeddings.shape}")
    
    # Handle 3D embeddings (Qwen returns 3D: batch x layers x dims)
    # Squeeze out batch dimension if it's 1
    if token_embeddings.ndim == 3:
        print(f"Detected 3D embedding (batch={token_embeddings.shape[0]}, layers={token_embeddings.shape[1]}, dims={token_embeddings.shape[2]})")
        # Take mean across all layers and batch
        token_embeddings = token_embeddings.reshape(-1, token_embeddings.shape[-1])  # Flatten to 2D
        print(f"Reshaped to 2D: {token_embeddings.shape}")
    
    print(f"Each embedding is {token_embeddings.shape[-1]} dimensions")
    
    # Step 3: Pool - take mean of all token embeddings
    # This combines all tokens into ONE embedding vector
    pooled = np.mean(token_embeddings, axis=0)
    print(f"Pooled embedding shape: {pooled.shape}")
    
    # Step 4: Normalize - make magnitude = 1
    # This scales the vector so its length is exactly 1.0
    norm_magnitude = np.linalg.norm(pooled)
    normalized = pooled / norm_magnitude
    
    print(f"Norm before normalize: {norm_magnitude}")
    print(f"Norm after normalize: {np.linalg.norm(normalized)}")
    
    return normalized

# Test it
print("Testing Qwen embedding normalization...\n")
embedding = get_embedding_normalized("Hello world")

print(f"\n{'='*50}")
print(f"Final embedding shape: {embedding.shape}")
print(f"Magnitude (should be 1.0): {np.linalg.norm(embedding)}")
print(f"First 10 dimensions: {embedding[:10]}")
print(f"{'='*50}")

# Test with different texts
print("\n\nTesting similarity between texts...")
emb1 = get_embedding_normalized("Hello world")
emb2 = get_embedding_normalized("Hi there world")
emb3 = get_embedding_normalized("The quick brown fox")

# Cosine similarity (dot product of normalized vectors)
sim_1_2 = np.dot(emb1, emb2)
sim_1_3 = np.dot(emb1, emb3)

print(f"\nSimilarity between 'Hello world' and 'Hi there world': {sim_1_2:.4f}")
print(f"Similarity between 'Hello world' and 'The quick brown fox': {sim_1_3:.4f}")
print(f"(Higher = more similar, range: -1 to 1)")