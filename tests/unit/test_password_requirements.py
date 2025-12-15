import pytest


def test_password_requirements():
    from core.services.auth.models import UserCreate

    # too short
    raised = False
    try:
        UserCreate(email="a@test.com", username="user123", password="Ab1")
    except Exception:
        raised = True
    assert raised is True

    # missing uppercase
    raised = False
    try:
        UserCreate(email="a@test.com", username="user123", password="lowercase1")
    except Exception:
        raised = True
    assert raised is True

    # missing digit
    raised = False
    try:
        UserCreate(email="a@test.com", username="user123", password="Uppercase")
    except Exception:
        raised = True
    assert raised is True

    # valid
    model = UserCreate(email="a@test.com", username="user123", password="Goodpass1")
    assert model.email == "a@test.com"


@pytest.mark.asyncio
async def test_user_service_rejects_weak_password():
    from core.services.auth.user_service import UserService

    class FakeRepo:
        async def user_exists(self, email: str) -> bool:
            return False

        async def create_user(self, *args, **kwargs):
            raise AssertionError("create_user should not be called for weak passwords")

    svc = UserService(user_repository=FakeRepo())
    user_id = await svc.create_user(email="weak@test.com", password="lowercase1", role="user")
    assert user_id is None
