import pytest


@pytest.mark.asyncio
async def test_user_registration(async_client, unique_email):
    # AUTH-I01
    resp = await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "user",
            "redirect": "/",
        },
    )
    assert resp.status_code == 303
    # Should set auth_token cookie on successful auto-login
    assert "auth_token=" in (resp.headers.get("set-cookie") or "")


@pytest.mark.asyncio
async def test_user_login(async_client, unique_email):
    # AUTH-I02
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "user",
            "redirect": "/",
        },
    )

    # clear cookies to test login flow explicitly
    async_client.cookies.clear()

    resp = await async_client.post(
        "/auth/login",
        data={"email": unique_email, "password": "Goodpass1", "redirect": "/"},
    )
    assert resp.status_code == 303
    assert "auth_token=" in (resp.headers.get("set-cookie") or "")


@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client, unique_email):
    # AUTH-I03
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "user",
            "redirect": "/",
        },
    )

    async_client.cookies.clear()

    resp = await async_client.post(
        "/auth/login",
        data={"email": unique_email, "password": "Wrongpass1", "redirect": "/"},
    )
    assert resp.status_code == 303
    assert resp.headers.get("location", "").startswith("/auth?tab=login")
    assert "auth_token=" not in (resp.headers.get("set-cookie") or "")


@pytest.mark.asyncio
async def test_admin_login(async_client, unique_email):
    # AUTH-I04
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

    resp = await async_client.post(
        "/admin/auth/login",
        data={"email": unique_email, "password": "Goodpass1", "redirect": "/admin/dashboard"},
    )
    assert resp.status_code == 303
    assert resp.headers.get("location") == "/admin/dashboard"
    assert "auth_token=" in (resp.headers.get("set-cookie") or "")


@pytest.mark.asyncio
async def test_admin_login_non_admin(async_client, unique_email):
    # AUTH-I05
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "user",
            "redirect": "/",
        },
    )

    async_client.cookies.clear()

    resp = await async_client.post(
        "/admin/auth/login",
        data={"email": unique_email, "password": "Goodpass1", "redirect": "/admin/dashboard"},
    )
    assert resp.status_code == 303
    assert resp.headers.get("location", "").startswith("/admin/login?error=Admin+access+required")
    assert "auth_token=" not in (resp.headers.get("set-cookie") or "")


@pytest.mark.asyncio
async def test_logout(async_client, unique_email):
    # AUTH-I06
    resp = await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "user",
            "redirect": "/",
        },
    )
    assert resp.status_code == 303
    assert "auth_token=" in (resp.headers.get("set-cookie") or "")

    # cookie jar should already have it
    assert async_client.cookies.get("auth_token")

    resp2 = await async_client.post("/auth/logout")
    assert resp2.status_code == 303
    # cookie deletion header should be present
    assert "auth_token=" in (resp2.headers.get("set-cookie") or "")


@pytest.mark.asyncio
async def test_get_current_user(async_client, unique_email):
    # AUTH-I07
    resp = await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "user",
            "redirect": "/",
        },
    )
    assert async_client.cookies.get("auth_token")

    dash = await async_client.get("/dashboard")
    assert dash.status_code == 200
    body = dash.text
    assert unique_email in body
