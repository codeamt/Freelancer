import pytest

@pytest.mark.asyncio
async def test_register_and_login(async_client):
    register_data = {"username": "asyncuser", "email": "async@example.com", "password": "testpass"}
    response = await async_client.post("/auth/register", json=register_data)
    assert response.status_code == 201
    assert "user_id" in response.json()

    login_data = {"email": "async@example.com", "password": "testpass"}
    response = await async_client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()