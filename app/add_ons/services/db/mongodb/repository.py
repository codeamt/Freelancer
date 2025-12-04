# app/add_ons/services/mongodb/repository.py
from motor.motor_asyncio import AsyncIOMotorCollection
from core.db.interfaces.base_repository import BaseRepository
from typing import Dict, List, Optional, AsyncIterator
import os

class MongoDBRepository(BaseRepository):
    """MongoDB implementation of BaseRepository"""
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def get(self, id: str) -> Optional[Dict]:
        return await self.collection.find_one({"_id": id})

    async def get_bulk(self, ids: List[str]) -> Dict[str, Dict]:
        cursor = self.collection.find({"_id": {"$in": ids}})
        return {doc["_id"]: doc async for doc in cursor}

    async def save(self, entity: Dict) -> Dict:
        result = await self.collection.insert_one(entity)
        entity["_id"] = result.inserted_id
        return entity

    async def save_bulk(self, entities: List[Dict]) -> List[Dict]:
        result = await self.collection.insert_many(entities)
        for entity, id in zip(entities, result.inserted_ids):
            entity["_id"] = id
        return entities

    async def stream_all(self) -> AsyncIterator[Dict]:
        async for document in self.collection.find():
            yield document