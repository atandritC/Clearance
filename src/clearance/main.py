from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from clearance.config import settings
from clearance.database import get_db_session
from clearance.models import User
from clearance.models import KnowledgeDocument, KnowledgeDocumentGrant
from clearance.security import create_access_token, verify_password
from clearance.users import find_user_by_email
from clearance.schemas import (
    DemoSearchResponse,
    DemoUserResponse,
    RetrievedChunkResponse,
)
from clearance.auth import get_current_admin_user, get_current_demo_user, get_current_user
from clearance.assistant.answer import answer_question
from clearance.assistant.schemas import (
    AccessTokenResponse,
    AssistantAnswerRequest,
    AssistantAnswerResponse,
    DocumentGrantCreateRequest,
    DocumentGrantResponse,
    LoginRequest,
)
from clearance.llm.errors import LLMProviderError, LLMRateLimitError
from clearance.retrieval.search import search_documents

app = FastAPI(title="Clearance")

if settings.allowed_frontend_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_frontend_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Demo-User-ID"],
    )


@app.post("/auth/login", response_model=AccessTokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AccessTokenResponse:
    user = await find_user_by_email(session, request.email.strip().lower())
    if (
        user is None
        or not user.is_active
        or not verify_password(request.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=401,
            detail="Email or password is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id)
    return AccessTokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@app.get("/auth/me", response_model=DemoUserResponse)
async def authenticated_user(
    user: User = Depends(get_current_user),
) -> dict[str, int | str | bool]:
    return {
        "id": user.id,
        "display_name": user.display_name,
        "role": user.role,
        "department": user.department,
        "is_admin": user.is_admin,
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def readiness_check(
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503, detail="Database is not available"
        ) from error

    return {"status": "ready"}


@app.get("/demo/whoami", response_model=DemoUserResponse)
async def demo_whoami(
    user: User = Depends(get_current_demo_user),
) -> dict[str, int | str]:

    return {
        "id": user.id,
        "display_name": user.display_name,
        "role": user.role,
        "department": user.department,
    }


@app.get("/demo/users", response_model=list[DemoUserResponse])
async def list_demo_users(
    session: AsyncSession = Depends(get_db_session),
) -> list[dict[str, int | str]]:
    if not settings.demo_mode:
        raise HTTPException(status_code=404, detail="Not found")

    result = await session.scalars(
        select(User).where(User.is_active.is_(True)).order_by(User.id)
    )

    return [
        {
            "id": user.id,
            "display_name": user.display_name,
            "role": user.role,
            "department": user.department,
        }
        for user in result.all()
    ]


@app.get("/demo/search", response_model=DemoSearchResponse)
async def demo_search(
    question: str = Query(min_length=3, max_length=500),
    user: User = Depends(get_current_demo_user),
    session: AsyncSession = Depends(get_db_session),
) -> DemoSearchResponse:
    points = await search_documents(question, user, session)

    return DemoSearchResponse(
        question=question,
        results=[
            RetrievedChunkResponse(
                score=point.score,
                **(point.payload or {}),
            )
            for point in points
        ],
    )


@app.post("/demo/ask", response_model=AssistantAnswerResponse)
async def demo_ask(
    request: AssistantAnswerRequest,
    user: User = Depends(get_current_demo_user),
    session: AsyncSession = Depends(get_db_session),
) -> AssistantAnswerResponse:
    return await run_ask(request.question, user, session, request.confirm_actions)


@app.post("/api/ask", response_model=AssistantAnswerResponse)
async def authenticated_ask(
    request: AssistantAnswerRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> AssistantAnswerResponse:
    return await run_ask(request.question, user, session, request.confirm_actions)


async def run_ask(
    question: str,
    user: User,
    session: AsyncSession,
    confirm_actions: bool = False,
) -> AssistantAnswerResponse:
    try:
        return await answer_question(question, user, session, confirm_actions)
    except LLMRateLimitError as error:
        headers = {"Retry-After": error.retry_after} if error.retry_after else None
        raise HTTPException(
            status_code=503,
            detail="The answer service is temporarily busy. Please try again shortly.",
            headers=headers,
        ) from error
    except LLMProviderError as error:
        raise HTTPException(
            status_code=502,
            detail="The answer service could not complete the request.",
        ) from error


@app.get(
    "/api/admin/documents/{document_id}/versions/{version}/grants",
    response_model=list[DocumentGrantResponse],
)
async def list_document_grants(
    document_id: str,
    version: str,
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
) -> list[DocumentGrantResponse]:
    document = await find_document_version(session, document_id, version)
    if document is None:
        raise HTTPException(status_code=404, detail="Document version not found")
    result = await session.scalars(
        select(KnowledgeDocumentGrant)
        .where(KnowledgeDocumentGrant.knowledge_document_id == document.id)
        .order_by(KnowledgeDocumentGrant.user_id)
    )
    return [
        DocumentGrantResponse(
            document_id=document.document_id,
            version=document.version,
            user_id=grant.user_id,
            granted_by_user_id=grant.granted_by_user_id,
            granted_at=grant.granted_at,
        )
        for grant in result.all()
    ]


@app.post(
    "/api/admin/documents/{document_id}/versions/{version}/grants",
    response_model=DocumentGrantResponse,
)
async def create_document_grant(
    document_id: str,
    version: str,
    request: DocumentGrantCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
) -> DocumentGrantResponse:
    document = await find_active_document(session, document_id, version)
    if document is None:
        raise HTTPException(status_code=404, detail="Active document version not found")
    if document.access_level != "restricted":
        raise HTTPException(
            status_code=400,
            detail="Per-user grants are only needed for restricted documents",
        )
    recipient = await session.get(User, request.user_id)
    if recipient is None or not recipient.is_active:
        raise HTTPException(status_code=404, detail="Active user not found")

    grant = await session.scalar(
        select(KnowledgeDocumentGrant).where(
            KnowledgeDocumentGrant.knowledge_document_id == document.id,
            KnowledgeDocumentGrant.user_id == recipient.id,
        )
    )
    if grant is None:
        grant = KnowledgeDocumentGrant(
            knowledge_document_id=document.id,
            user_id=recipient.id,
            granted_by_user_id=admin.id,
        )
        session.add(grant)
        await session.commit()
        await session.refresh(grant)

    return DocumentGrantResponse(
        document_id=document.document_id,
        version=document.version,
        user_id=grant.user_id,
        granted_by_user_id=grant.granted_by_user_id,
        granted_at=grant.granted_at,
    )


@app.delete(
    "/api/admin/documents/{document_id}/versions/{version}/grants/{user_id}",
    response_model=dict[str, str],
)
async def remove_document_grant(
    document_id: str,
    version: str,
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
) -> dict[str, str]:
    document = await find_document_version(session, document_id, version)
    if document is None:
        raise HTTPException(status_code=404, detail="Document version not found")
    grant = await session.scalar(
        select(KnowledgeDocumentGrant).where(
            KnowledgeDocumentGrant.knowledge_document_id == document.id,
            KnowledgeDocumentGrant.user_id == user_id,
        )
    )
    if grant is None:
        raise HTTPException(status_code=404, detail="Document grant not found")
    await session.delete(grant)
    await session.commit()
    return {"status": "revoked"}


async def find_active_document(
    session: AsyncSession,
    document_id: str,
    version: str,
) -> KnowledgeDocument | None:
    return await session.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.document_id == document_id,
            KnowledgeDocument.version == version,
            KnowledgeDocument.status == "active",
        )
    )


async def find_document_version(
    session: AsyncSession,
    document_id: str,
    version: str,
) -> KnowledgeDocument | None:
    return await session.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.document_id == document_id,
            KnowledgeDocument.version == version,
        )
    )
