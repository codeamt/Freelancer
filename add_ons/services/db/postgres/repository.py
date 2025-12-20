# app/add_ons/services/postgres/repository.py
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from core.db.interfaces.base_repository import BaseRepository

class PostgresRepository(BaseRepository):
    """Postgres implementation of BaseRepository"""
    def __init__(self, session: AsyncSession, model):
        self.session = session
        self.model = model

    async def get(self, id: str) -> Optional[Any]:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()

    async def get_bulk(self, ids: List[str]) -> Dict[str, Any]:
        result = await self.session.execute(
            select(self.model).where(self.model.id.in_(ids))
        )
        return {entity.id: entity for entity in result.scalars()}

    async def save_bulk(self, entities: List[Any]) -> List[Any]:
        self.session.add_all(entities)
        await self.session.flush()
        return entities

    async def update_bulk(self, updates: Dict[str, Dict[str, Any]]) -> int:
        stmt = update(self.model)
        await self.session.execute(stmt, [
            {"id": id, **values} for id, values in updates.items()
        ])
        return len(updates)