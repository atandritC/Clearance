from qdrant_client import AsyncQdrantClient, models
from clearance.config import settings


def create_qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(url=settings.qdrant_url)


async def ensure_document_collection() -> None:
    client = create_qdrant_client()

    try:
        if await client.collection_exists(settings.qdrant_collection):
            print("The document collection already exists.")
            return

        await client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE,
            ),
        )
        print("Created the document collection.")
    finally:
        await client.close()
