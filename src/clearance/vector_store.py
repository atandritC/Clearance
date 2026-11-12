from qdrant_client import AsyncQdrantClient, models
from clearance.config import settings


def create_qdrant_client() -> AsyncQdrantClient:
    api_key = (
        settings.qdrant_api_key.get_secret_value()
        if settings.qdrant_api_key is not None
        else None
    )
    return AsyncQdrantClient(url=settings.qdrant_url, api_key=api_key)


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
