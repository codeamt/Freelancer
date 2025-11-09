import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.mark.asyncio
async def test_database_and_cache_integration():
    async with PostgresContainer("postgres:15-alpine") as postgres, RedisContainer("redis:7-alpine") as redis:
        db_url = postgres.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")
        engine = create_async_engine(db_url, echo=True)

        async with engine.begin() as conn:
            await conn.run_sync(lambda c: c.execute("SELECT 1"))

        redis_url = redis.get_connection_url()
        assert "redis://" in redis_url