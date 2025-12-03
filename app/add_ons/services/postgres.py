"""
PostgreSQL Service - Relational database for structured data.
Used by: Commerce, LMS, Auth
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import Optional, Dict
import os

class PostgresService:
    """
    Universal PostgreSQL service.
    Domains can extend for custom queries.
    """
    
    def __init__(self, uri: Optional[str] = None):
        self.uri = uri or os.getenv("POSTGRES_URI", "postgresql+asyncpg://localhost/fastapp")
        self.engine = None
        self.session_factory = None
    
    async def connect(self):
        """Initialize connection pool"""
        if not self.engine:
            self.engine = create_async_engine(self.uri, echo=False)
            self.session_factory = sessionmaker(
                self.engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
        return self.engine
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.session_factory:
            await self.connect()
        return self.session_factory()
    
    async def execute(self, query: str, params: Dict = None):
        """Execute raw SQL"""
        async with await self.get_session() as session:
            result = await session.execute(query, params or {})
            await session.commit()
            return result