import asyncio
from qdrant_client import AsyncQdrantClient

async def main():
    client = AsyncQdrantClient(":memory:")
    methods = sorted([m for m in dir(client) if not m.startswith("_")])
    print("Methods available on AsyncQdrantClient:")
    for m in methods:
        print(f"  - {m}")
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
