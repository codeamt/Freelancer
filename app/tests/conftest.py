import os
import pytest
import asyncio
from httpx import AsyncClient
from fastapi import FastAPI
from app.main import app

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def async_client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

@pytest.fixture(scope="session")
def test_env(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("fastapp_test")
    os.environ["TEST_TMP"] = str(tmp_dir)
    yield tmp_dir