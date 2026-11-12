import asyncio

from clearance.vector_store import ensure_document_collection

if __name__ == "__main__":
    asyncio.run(ensure_document_collection())
