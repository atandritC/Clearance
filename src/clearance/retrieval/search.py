from qdrant_client.models import ScoredPoint
from sqlalchemy.ext.asyncio import AsyncSession

from clearance.config import settings
from clearance.embeddings import embed_texts
from clearance.models import User
from clearance.retrieval.filters import build_document_filter
from clearance.retrieval.grants import get_granted_document_versions
from clearance.vector_store import create_qdrant_client


async def search_documents(
    question: str,
    user: User,
    session: AsyncSession,
    limit: int = 5,
) -> list[ScoredPoint]:
    question_vector = embed_texts([question])[0]

    granted_versions = await get_granted_document_versions(session, user.id)
    access_filter = build_document_filter(user, granted_versions)

    client = create_qdrant_client()
    try:
        results = await client.query_points(
            collection_name=settings.qdrant_collection,
            query=question_vector,
            query_filter=access_filter,
            score_threshold=settings.qdrant_score_threshold,
            limit=limit,
            with_payload=True,
        )

        return results.points
    finally:
        await client.close()
