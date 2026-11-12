from datetime import date

from pydantic import BaseModel


class DemoUserResponse(BaseModel):
    id: int
    display_name: str
    role: str
    department: str


class RetrievedChunkResponse(BaseModel):
    document_id: str
    version: str
    chunk_index: int
    title: str
    department: str
    access_level: str
    status: str
    effective_date: date
    text: str
    score: float


class DemoSearchResponse(BaseModel):
    question: str
    results: list[RetrievedChunkResponse]
