import pytest


def test_password_hashing():
    from core.utils.security import hash_password, verify_password

    password = "Admin123!"
    hashed = hash_password(password)

    assert isinstance(hashed, str)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_jwt_token_creation():
    from core.services.auth.providers.jwt import JWTProvider

    provider = JWTProvider()
    token = provider.create({"user_id": 123, "email": "a@test.com", "role": "admin"})

    assert isinstance(token, str)
    assert token.count(".") == 2


def test_jwt_token_verification():
    from core.services.auth.providers.jwt import JWTProvider

    provider = JWTProvider()
    token = provider.create({"user_id": 123, "email": "a@test.com", "role": "admin"})
    payload = provider.verify(token)

    assert payload is not None
    assert payload["user_id"] == 123
    assert payload["email"] == "a@test.com"
    assert payload["role"] == "admin"


def test_jwt_token_expiration():
    from core.services.auth.providers.jwt import JWTProvider

    provider = JWTProvider()

    # create a token that is already expired
    token = provider.create({"user_id": 1}, expires_hours=-1)

    # standard verify rejects
    assert provider.verify(token) is None

    # allow_expired returns payload
    payload = provider.verify(token, allow_expired=True)
    assert payload is not None
    assert payload.get("user_id") == 1


def test_user_role_enum():
    from core.services.auth.models import UserRole

    expected = {
        "super_admin",
        "admin",
        "editor",
        "member",
        "user",
        "instructor",
        "student",
        "shop_owner",
        "merchant",
        "course_creator",
    }

    assert {r.value for r in UserRole} == expected
