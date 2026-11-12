from qdrant_client import AsyncQdrantClient, models
from clearance.config import settings

DOCUMENT_PAYLOAD_INDEXES = {
    "document_id": models.PayloadSchemaType.KEYWORD,
    "version": models.PayloadSchemaType.KEYWORD,
    "status": models.PayloadSchemaType.KEYWORD,
    "access_level": models.PayloadSchemaType.KEYWORD,
    "department": models.PayloadSchemaType.KEYWORD,
}


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
        if not await client.collection_exists(settings.qdrant_collection):
            await client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE,
                ),
            )
            print("Created the document collection.")

        collection = await client.get_collection(settings.qdrant_collection)
        existing_indexes = collection.payload_schema or {}

        for field_name, field_schema in DOCUMENT_PAYLOAD_INDEXES.items():
            if field_name in existing_indexes:
                continue

            await client.create_payload_index(
                collection_name=settings.qdrant_collection,
                field_name=field_name,
                field_schema=field_schema,
                wait=True,
            )
            print(f"Created the {field_name} payload index.")
    finally:
        await client.close()
