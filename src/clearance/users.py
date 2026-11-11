from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from clearance.models import User


async def find_user_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email))


async def find_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)
