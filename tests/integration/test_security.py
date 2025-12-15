import pytest


@pytest.mark.asyncio
async def test_xss_prevention(async_client):
    # SEC-I01
    payload = "<script>alert(1)</script>"
    resp = await async_client.post("/_test/echo", data={"q": payload})
    assert resp.status_code == 200

    data = resp.json()
    sanitized = data["form"]["q"]

    # Should not contain raw tags
    assert "<" not in sanitized
    assert ">" not in sanitized
    # Should contain escaped representation (note: semicolons are stripped by sanitize_sql_input)
    assert "&ltscript&gt" in sanitized


@pytest.mark.asyncio
async def test_sql_injection_prevention(async_client):
    # SEC-I02
    payload = "1; DROP TABLE users; --"
    resp = await async_client.post("/_test/echo", data={"q": payload})
    assert resp.status_code == 200

    sanitized = resp.json()["form"]["q"]
    assert ";" not in sanitized
    assert "\\" not in sanitized
    assert "DROP TABLE" in sanitized


@pytest.mark.asyncio
async def test_rate_limiting(async_client):
    # SEC-I03
    # Rate limiter defaults to 60 req/min; 61 rapid requests should trigger 429.
    last_status = None
    for _ in range(65):
        r = await async_client.get("/_test/ping")
        last_status = r.status_code
        if last_status == 429:
            break

    assert last_status == 429


@pytest.mark.asyncio
async def test_httponly_cookie(async_client_production, unique_email):
    # SEC-I04
    resp = await async_client_production.post(
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

    set_cookie = resp.headers.get("set-cookie") or ""
    assert "auth_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
