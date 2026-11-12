import asyncio
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import models

from clearance.config import settings
from clearance.embeddings import embed_texts
from clearance.ingestion.chunking import chunk_documents
from clearance.ingestion.markdown import parse_knowledge_base
from clearance.vector_store import create_qdrant_client


async def main() -> None:
    source_path = (
        Path(__file__).resolve().parents[1] / "CLEARANCE_SYNTHETIC_KNOWLEDGE_BASE.md"
    )
    documents = parse_knowledge_base(source_path)
    chunks = chunk_documents(documents)

    vectors = embed_texts([chunk.text for chunk in chunks])

    points = []

    for chunk, vector in zip(chunks, vectors, strict=True):
        point_id = str(
            uuid5(
                NAMESPACE_URL,
                f"{chunk.document_id}:{chunk.version}:{chunk.chunk_index}",
            )
        )

        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "document_id": chunk.document_id,
                    "version": chunk.version,
                    "chunk_index": chunk.chunk_index,
                    "title": chunk.title,
                    "department": chunk.department,
                    "access_level": chunk.access_level,
                    "status": chunk.status,
                    "effective_date": chunk.effective_date.isoformat(),
                    "text": chunk.text,
                },
            )
        )

    client = create_qdrant_client()
    try:
        await client.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
            wait=True,
        )
    finally:
        await client.close()

    print(f"Uploaded {len(points)} chunks.")


if __name__ == "__main__":
    asyncio.run(main())
