import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from clearance.config import settings
from clearance.database import get_db_session
from clearance.models import User
from clearance.security import decode_access_token
from clearance.users import find_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    unauthorized = HTTPException(
        status_code=401,
        detail="Authentication is required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError as error:
        raise unauthorized from error

    user = await find_user_by_id(session, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


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
