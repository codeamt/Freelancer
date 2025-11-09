import pytest

@pytest.mark.asyncio
async def test_async_e2e_user_flow(async_client):
    user = {"username": "asyncflow", "email": "asyncflow@example.com", "password": "asyncpass"}
    register = await async_client.post("/auth/register", json=user)
    assert register.status_code == 201

    course = await async_client.post("/lms/courses", json={"title": "Async 101", "description": "E2E async test"})
    assert course.status_code == 201

    checkout = await async_client.post("/commerce/checkout", json={"product_id": 1, "quantity": 1})
    assert checkout.status_code == 200

    post = await async_client.post("/social/posts", json={"author_id": 1, "content": "Testing async end-to-end!"})
    assert post.status_code == 201

    dashboard = await async_client.get("/admin/kpi")
    assert dashboard.status_code == 200