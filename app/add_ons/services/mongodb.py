"""
MongoDB Service - Document database for flexible data.
Used by: Stream, Social, Analytics
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Any, Dict, List, Optional
from datetime import datetime
import os

class MongoDBService:
    """
    Universal MongoDB service.
    Domains can extend for custom operations.
    """
    
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = db_name or os.getenv("MONGO_DB_NAME", "fastapp")
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
    
    async def connect(self):
        """Establish connection"""
        if not self.client:
            self.client = AsyncIOMotorClient(self.uri, uuidRepresentation="standard")
            self.db = self.client[self.db_name]
        return self.db
    
    async def disconnect(self):
        if self.client:
            self.client.close()
    
    # Generic CRUD
    async def insert_one(self, collection: str, document: Dict[str, Any]):
        document["created_at"] = datetime.utcnow()
        result = await self.db[collection].insert_one(document)
        return str(result.inserted_id)
    
    async def find_one(self, collection: str, query: Dict[str, Any]):
        doc = await self.db[collection].find_one(query)
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc
    
    async def find_many(self, collection: str, query: Dict[str, Any], limit: int = 50):
        cursor = self.db[collection].find(query).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    
    async def update_one(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]):
        await self.db[collection].update_one(query, {"$set": data})
        return await self.find_one(collection, query)
    
    async def delete_one(self, collection: str, query: Dict[str, Any]):
        result = await self.db[collection].delete_one(query)
        return result.deleted_count
    
    async def aggregate(self, collection: str, pipeline: List[Dict[str, Any]]):
        cursor = self.db[collection].aggregate(pipeline)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
