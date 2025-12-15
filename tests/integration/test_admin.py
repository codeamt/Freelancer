import os
import pytest

if os.getenv("RUN_INTEGRATION_TESTS") != "1":
    pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.", allow_module_level=True)


@pytest.mark.asyncio
async def test_admin_login_page(async_client):
    resp = await async_client.get("/admin/login")
    assert resp.status_code == 200
    assert "Web Admin" in resp.text


@pytest.mark.asyncio
async def test_admin_dashboard_authenticated(async_client, unique_email):
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "admin",
            "redirect": "/",
        },
    )

    async_client.cookies.clear()
    login = await async_client.post(
        "/admin/auth/login",
        data={"email": unique_email, "password": "Goodpass1", "redirect": "/admin/dashboard"},
    )
    assert login.status_code == 303
    assert async_client.cookies.get("auth_token")

    dash = await async_client.get("/admin/dashboard")
    assert dash.status_code == 200


@pytest.mark.asyncio
async def test_admin_dashboard_unauthenticated(async_client):
    async_client.cookies.clear()
    resp = await async_client.get("/admin/dashboard")
    assert resp.status_code == 303
    assert resp.headers.get("location", "").startswith("/admin/login")


@pytest.mark.asyncio
async def test_role_based_nav_admin(async_client, unique_email):
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "admin",
            "redirect": "/",
        },
    )
    dash = await async_client.get("/admin/dashboard")
    assert dash.status_code in (200, 303)
    # If authenticated, nav should include admin dashboard link
    if dash.status_code == 200:
        assert "/admin/dashboard" in dash.text


@pytest.mark.asyncio
async def test_role_based_nav_instructor(async_client, unique_email):
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "instructor",
            "redirect": "/",
        },
    )

    page = await async_client.get("/lms-example/")
    assert page.status_code == 200
    assert "/lms-example/instructor" in page.text


@pytest.mark.asyncio
async def test_role_based_nav_shop_owner(async_client, unique_email):
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "shop_owner",
            "redirect": "/",
        },
    )

    page = await async_client.get("/eshop-example/")
    assert page.status_code == 200
    assert "/eshop-example/admin" in page.text
