from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import pytest

from clearance import auth
from clearance.models import User
from clearance.security import create_access_token, hash_password


def make_user(is_active: bool = True) -> User:
    return User(
        id=23,
        email="engineer@astervale.example",
        display_name="Demo Engineer",
        role="engineer",
        department="IT Operations",
        is_active=is_active,
        hashed_password=hash_password("fictional-demo-password"),
    )


@pytest.mark.asyncio
async def test_current_user_is_loaded_from_database(monkeypatch: pytest.MonkeyPatch) -> None:
    user = make_user()

    async def find_user(session: object, user_id: int) -> User:
        assert user_id == user.id
        return user

    monkeypatch.setattr(auth, "find_user_by_id", find_user)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=create_access_token(user.id),
    )

    current_user = await auth.get_current_user(credentials, object())

    assert current_user is user


@pytest.mark.asyncio
async def test_inactive_user_cannot_use_valid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    user = make_user(is_active=False)

    async def find_user(session: object, user_id: int) -> User:
        return user

    monkeypatch.setattr(auth, "find_user_by_id", find_user)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=create_access_token(user.id),
    )

    with pytest.raises(HTTPException) as error:
        await auth.get_current_user(credentials, object())

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_non_admin_user_cannot_manage_document_grants() -> None:
    user = make_user()

    with pytest.raises(HTTPException) as error:
        await auth.get_current_admin_user(user)

    assert error.value.status_code == 403
