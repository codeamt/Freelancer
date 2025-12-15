import os
import uuid

import pytest


@pytest.fixture(scope="session")
def postgres_url() -> str:
    # Matches docker-compose.yml default
    return os.getenv(
        "POSTGRES_URL",
        "postgresql://postgres:postgres@localhost:5432/app_db",
    )


@pytest.fixture()
async def postgres_adapter(postgres_url: str):
    from core.db.adapters.postgres_adapter import PostgresAdapter

    pg = PostgresAdapter(connection_string=postgres_url, min_size=1, max_size=2)
    try:
        await pg.connect()
    except Exception as e:
        pytest.skip(f"Postgres not reachable at {postgres_url}: {e}")

    try:
        # Ensure schema exists for repository tests
        from core.db.init_schema import CORE_SCHEMA_SQL

        await pg.execute(CORE_SCHEMA_SQL)
        yield pg
    finally:
        await pg.disconnect()


@pytest.fixture()
def unique_email() -> str:
    return f"pytest-{uuid.uuid4().hex[:12]}@test.com"


@pytest.mark.asyncio
async def test_postgres_connection(postgres_adapter):
    # DB-U01
    row = await postgres_adapter.fetch_one("SELECT 1 AS ok")
    assert row is not None
    assert row["ok"] == 1


@pytest.mark.asyncio
async def test_user_repository_create(postgres_adapter, unique_email):
    # DB-U02
    from core.db.repositories.user_repository import UserRepository

    repo = UserRepository(postgres=postgres_adapter)
    user_id = await repo.create_user(email=unique_email, password="Admin123!", role="user")

    assert isinstance(user_id, int)
    assert user_id > 0


@pytest.mark.asyncio
async def test_user_repository_get_by_email(postgres_adapter, unique_email):
    # DB-U03
    from core.db.repositories.user_repository import UserRepository

    repo = UserRepository(postgres=postgres_adapter)
    user_id = await repo.create_user(email=unique_email, password="Admin123!", role="user")

    data = await repo.get_user_by_email(unique_email)
    assert data is not None
    assert data["id"] == user_id
    assert data["email"] == unique_email
    assert data["role"] == "user"


@pytest.mark.asyncio
async def test_user_repository_verify_password(postgres_adapter, unique_email):
    # DB-U04
    from core.db.repositories.user_repository import UserRepository

    repo = UserRepository(postgres=postgres_adapter)
    await repo.create_user(email=unique_email, password="Admin123!", role="user")

    ok_user = await repo.verify_password(unique_email, "Admin123!")
    bad_user = await repo.verify_password(unique_email, "WrongPass123!")

    assert ok_user is not None
    assert ok_user.email == unique_email
    assert bad_user is None
