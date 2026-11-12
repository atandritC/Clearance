from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from clearance.config import settings
from clearance.database import get_db_session
from clearance.models import User
from clearance.schemas import (
    DemoSearchResponse,
    DemoUserResponse,
    RetrievedChunkResponse,
)
from clearance.auth import get_current_demo_user
from clearance.retrieval.search import search_documents

app = FastAPI(title="Clearance")


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
