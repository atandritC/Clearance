from datetime import date, datetime

from pydantic import BaseModel, Field


class AssistantAnswerRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    confirm_actions: bool = False


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class DocumentGrantCreateRequest(BaseModel):
    user_id: int = Field(gt=0)


class DocumentGrantResponse(BaseModel):
    document_id: str
    version: str
    user_id: int
    granted_by_user_id: int | None
    granted_at: datetime


class AnswerDraft(BaseModel):
    answer: str
    citation_ids: list[str]
    tool_result_ids: list[str]
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


class ToolResultResponse(BaseModel):
    result_id: str
    tool_name: str
    data: dict[str, object]


class AssistantAnswerResponse(BaseModel):
    question: str
    answer: str
    abstained: bool
    citations: list[AnswerCitation]
    tool_results: list[ToolResultResponse] = Field(default_factory=list)
