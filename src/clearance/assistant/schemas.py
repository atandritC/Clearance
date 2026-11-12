from datetime import date

from pydantic import BaseModel, Field


class AssistantAnswerRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AnswerDraft(BaseModel):
    answer: str
    citation_ids: list[str]
    abstain: bool


class AnswerCitation(BaseModel):
    chunk_id: str
    document_id: str
    version: str
    chunk_index: int
    title: str
    department: str
    effective_date: date
    excerpt: str


class AssistantAnswerResponse(BaseModel):
    question: str
    answer: str
    abstained: bool
    citations: list[AnswerCitation]
