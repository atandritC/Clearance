from dataclasses import dataclass
from datetime import date

from clearance.ingestion.markdown import ParsedDocument


@dataclass
class DocumentChunk:
    document_id: str
    version: str
    chunk_index: int
    title: str
    department: str
    access_level: str
    status: str
    effective_date: date
    text: str


def split_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[str]:
    text = " ".join(text.split())

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            space = text.rfind(" ", start, end)
            if space > start:
                end = space

        chunks.append(text[start:end].strip())

        if end == len(text):
            break

        start = end - overlap

    return chunks


def chunk_documents(
    documents: list[ParsedDocument],
) -> list[DocumentChunk]:
    chunks = []

    for document in documents:
        for index, text in enumerate(split_text(document.body)):
            chunks.append(
                DocumentChunk(
                    document_id=document.document_id,
                    version=document.version,
                    chunk_index=index,
                    title=document.title,
                    department=document.department,
                    access_level=document.access_level,
                    status=document.status,
                    effective_date=document.effective_date,
                    text=text,
                )
            )

    return chunks
