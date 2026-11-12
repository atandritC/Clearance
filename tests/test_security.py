import jwt
import pytest

from clearance.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_can_be_verified_without_storing_plaintext() -> None:
    password = "fictional-demo-password"
    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password) is True
    assert verify_password("another-password", hashed_password) is False
    assert verify_password("any-password", "!") is False


def test_access_token_contains_a_valid_user_identity() -> None:
    token = create_access_token(23)

    assert decode_access_token(token) == 23


def test_invalid_access_token_is_rejected() -> None:
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not-a-token")
