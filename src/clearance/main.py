from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from clearance.config import settings
from clearance.database import get_db_session
from clearance.models import User
from clearance.security import create_access_token, verify_password
from clearance.users import find_user_by_email
from clearance.schemas import (
    DemoSearchResponse,
    DemoUserResponse,
    RetrievedChunkResponse,
)
from clearance.auth import get_current_demo_user, get_current_user
from clearance.assistant.answer import answer_question
from clearance.assistant.schemas import (
    AccessTokenResponse,
    AssistantAnswerRequest,
    AssistantAnswerResponse,
    LoginRequest,
)
from clearance.llm.errors import LLMProviderError, LLMRateLimitError
from clearance.retrieval.search import search_documents

app = FastAPI(title="Clearance")


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
) -> dict[str, int | str]:
    return {
        "id": user.id,
        "display_name": user.display_name,
        "role": user.role,
        "department": user.department,
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
) -> DemoSearchResponse:
    points = await search_documents(question, user)

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
) -> AssistantAnswerResponse:
    return await run_ask(request.question, user)


@app.post("/api/ask", response_model=AssistantAnswerResponse)
async def authenticated_ask(
    request: AssistantAnswerRequest,
    user: User = Depends(get_current_user),
) -> AssistantAnswerResponse:
    return await run_ask(request.question, user)


async def run_ask(question: str, user: User) -> AssistantAnswerResponse:
    try:
        return await answer_question(question, user)
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
