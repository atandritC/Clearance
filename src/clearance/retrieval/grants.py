from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from clearance.models import KnowledgeDocument, KnowledgeDocumentGrant


async def get_granted_document_versions(
    session: AsyncSession,
    user_id: int,
) -> set[tuple[str, str]]:
    result = await session.execute(
        select(KnowledgeDocument.document_id, KnowledgeDocument.version)
        .join(
            KnowledgeDocumentGrant,
            KnowledgeDocumentGrant.knowledge_document_id == KnowledgeDocument.id,
        )
        .where(
            KnowledgeDocumentGrant.user_id == user_id,
            KnowledgeDocument.status == "active",
        )
    )
    return set(result.all())
