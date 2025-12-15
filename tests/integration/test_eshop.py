import os
import pytest

if os.getenv("RUN_INTEGRATION_TESTS") != "1":
    pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.", allow_module_level=True)


@pytest.mark.asyncio
async def test_product_catalog_page(async_client):
    resp = await async_client.get("/eshop-example/")
    assert resp.status_code == 200
    assert "E-Shop Demo" in resp.text


@pytest.mark.asyncio
async def test_product_detail_page(async_client):
    resp = await async_client.get("/eshop-example/product/1")
    assert resp.status_code == 200
    assert "Low Tops" in resp.text


@pytest.mark.asyncio
async def test_add_to_cart(async_client, unique_email):
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
    resp = await async_client.post("/eshop-example/cart/add/1")
    assert resp.status_code == 200
    assert "added to cart" in resp.text.lower()


@pytest.mark.asyncio
async def test_view_cart(async_client, unique_email):
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
    await async_client.post("/eshop-example/cart/add/1")
    page = await async_client.get("/eshop-example/cart")
    assert page.status_code == 200
    assert "Your Cart" in page.text
    assert "Low Tops" in page.text


@pytest.mark.asyncio
async def test_checkout_flow(async_client, unique_email):
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

    # Checkout requires a non-empty cart; otherwise it redirects to /eshop-example/cart
    await async_client.post("/eshop-example/cart/add/1")

    resp = await async_client.get("/eshop-example/checkout")
    assert resp.status_code == 200
    assert "Checkout" in resp.text


@pytest.mark.asyncio
async def test_shop_admin_access(async_client, unique_email):
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
    resp = await async_client.get("/eshop-example/admin")
    assert resp.status_code == 200
    assert "Access Denied" not in resp.text


@pytest.mark.asyncio
async def test_shop_admin_denied(async_client, unique_email):
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
    resp = await async_client.get("/eshop-example/admin")
    assert resp.status_code == 200
    assert "Access Denied" in resp.text
