from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from clearance.config import settings
from clearance.database import get_db_session
from clearance.models import User
from clearance.schemas import DemoUserResponse
from clearance.auth import get_current_demo_user

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

    # Get active demo users, ordered by their ID.
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
