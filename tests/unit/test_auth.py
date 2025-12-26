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


def test_jwt_token_with_multi_role():
    """Test JWT token with multiple roles and versioning"""
    from core.services.auth.providers.jwt import JWTProvider

    provider = JWTProvider()
    token = provider.create({
        "user_id": 123,
        "email": "a@test.com",
        "role": "admin",
        "roles": ["admin", "instructor"],
        "role_version": 1
    })

    assert isinstance(token, str)
    assert token.count(".") == 2
    
    # Verify token contains multi-role data
    payload = provider.verify(token)
    assert payload is not None
    assert payload["roles"] == ["admin", "instructor"]
    assert payload["role_version"] == 1


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
        "user",
        "instructor",
        "student",
        "guest",
        "blog_admin",
        "blog_author",
        "lms_admin",
    }

    assert {r.value for r in UserRole} == expected


def test_user_role_hierarchy():
    """Test role hierarchy ordering"""
    from core.services.auth.role_hierarchy import RoleHierarchy
    from core.services.auth.models import UserRole
    
    # Test that higher level roles have precedence
    admin_level = RoleHierarchy.get_hierarchy_level(UserRole.ADMIN)
    user_level = RoleHierarchy.get_hierarchy_level(UserRole.USER)
    
    assert admin_level > user_level
    
    # Test primary role selection
    roles = [UserRole.USER, UserRole.INSTRUCTOR, UserRole.ADMIN]
    primary = RoleHierarchy.get_primary_role(roles)
    assert primary == UserRole.ADMIN
