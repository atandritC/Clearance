import asyncio
from pathlib import Path

from sqlalchemy import select

from clearance.database import SessionFactory, engine
from clearance.ingestion.markdown import parse_knowledge_base
from clearance.models import KnowledgeDocument


async def main() -> None:
    source_path = (
        Path(__file__).resolve().parents[1] / "CLEARANCE_SYNTHETIC_KNOWLEDGE_BASE.md"
    )
    documents = parse_knowledge_base(source_path)

    async with SessionFactory() as session:
        result = await session.scalars(select(KnowledgeDocument))
        existing = {(row.document_id, row.version): row for row in result.all()}

        added_count = 0

        for document in documents:
            key = (document.document_id, document.version)

            values = {
                "document_id": document.document_id,
                "title": document.title,
                "department": document.department,
                "access_level": document.access_level,
                "version": document.version,
                "status": document.status,
                "effective_date": document.effective_date,
            }

            row = existing.get(key)

            if row is None:
                session.add(KnowledgeDocument(**values))
                added_count += 1
            else:
                for field, value in values.items():
                    setattr(row, field, value)

        await session.commit()
        print(f"Processed {len(documents)} versions; added {added_count} new records.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
