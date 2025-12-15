import os
import pytest

if os.getenv("RUN_INTEGRATION_TESTS") != "1":
    pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.", allow_module_level=True)


@pytest.mark.asyncio
async def test_course_catalog_page(async_client):
    resp = await async_client.get("/lms-example/")
    assert resp.status_code == 200
    assert "Learn Anything" in resp.text


@pytest.mark.asyncio
async def test_course_detail_page(async_client):
    resp = await async_client.get("/lms-example/course/1")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_course_enrollment(async_client, unique_email):
    # Use a free course to avoid checkout flow.
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "student",
            "redirect": "/",
        },
    )
    resp = await async_client.post("/lms-example/enroll/1")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_lesson_view(async_client, unique_email):
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "student",
            "redirect": "/",
        },
    )
    await async_client.post("/lms-example/enroll/1")
    page = await async_client.get("/lms-example/student/course/1?lesson=1")
    assert page.status_code == 200
    assert "Lesson 1" in page.text


@pytest.mark.asyncio
async def test_instructor_dashboard(async_client, unique_email):
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
    resp = await async_client.get("/lms-example/instructor")
    assert resp.status_code == 200
    assert "Access Denied" not in resp.text


@pytest.mark.asyncio
async def test_instructor_denied(async_client, unique_email):
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "student",
            "redirect": "/",
        },
    )
    resp = await async_client.get("/lms-example/instructor")
    assert resp.status_code == 200
    assert "Access Denied" in resp.text


@pytest.mark.asyncio
async def test_cart_add_paid_course(async_client, unique_email):
    # Choose a likely paid course id. If course 1 is free, paid is often 2.
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "student",
            "redirect": "/",
        },
    )
    resp = await async_client.post("/lms-example/cart/add/2")
    assert resp.status_code == 200
