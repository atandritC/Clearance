from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from clearance.config import settings
from clearance.database import get_db_session
from clearance.models import User
from clearance.users import find_user_by_id


async def get_current_demo_user(
    demo_user_id: int = Header(alias="X-Demo-User-ID"),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    if not settings.demo_mode:
        raise HTTPException(status_code=404, detail="Not found")

    user = await find_user_by_id(session, demo_user_id)

    if user is None or not user.is_active:
        raise HTTPException(status_code=404, detail="Demo user not found")

    return user
