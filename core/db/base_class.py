"""
SQLAlchemy Base and Session Setup

Used for:
- Alembic migrations (Base)
- Optional ORM queries (async_session_maker)
- Schema definitions

Note: Repositories use raw SQL adapters, not this session maker.
"""
import os
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db"
)

# Declarative Base for ORM models
Base = declarative_base()

# Async engine for SQLAlchemy ORM (optional use)
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    future=True,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Session maker for ORM operations (optional use)
async_session_maker = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_orm_session() -> AsyncSession:
    """
    Get SQLAlchemy ORM session (optional).
    
    Most code should use repositories/adapters instead.
    This is here for backwards compatibility or special ORM needs.
    """
    async with async_session_maker() as session:
        yield session


# Alias for backwards compatibility
get_session = get_orm_session


async def init_db():
    """Initialize database tables (creates all ORM models)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Drop all database tables (dangerous!)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)