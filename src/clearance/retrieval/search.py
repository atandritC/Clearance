from qdrant_client.models import ScoredPoint

from clearance.config import settings
from clearance.embeddings import embed_texts
from clearance.models import User
from clearance.retrieval.filters import build_document_filter
from clearance.vector_store import create_qdrant_client


async def search_documents(
    question: str,
    user: User,
    limit: int = 5,
) -> list[ScoredPoint]:
    question_vector = embed_texts([question])[0]

    access_filter = build_document_filter(user)

    client = create_qdrant_client()
    try:
        results = await client.query_points(
            collection_name=settings.qdrant_collection,
            query=question_vector,
            query_filter=access_filter,
            limit=limit,
            with_payload=True,
        )

        return results.points
    finally:
        await client.close()
