"""MongoDB Adapter - Handles document/unstructured data"""
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import WriteConcern
from core.utils.logger import get_logger

logger = get_logger(__name__)


class MongoDBAdapter:
    """
    MongoDB adapter for document storage and flexible schemas.
    
    Use for: Unstructured data, nested documents, flexible schemas, user-generated content
    """
    
    def __init__(self, connection_string: str, database: str):
        self.connection_string = connection_string
        self.database_name = database
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._sessions: Dict[str, Any] = {}
        
    async def connect(self):
        """Connect to MongoDB"""
        if not self.client:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            logger.info(f"MongoDB connected to database: {self.database_name}")
            
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            
    # Transaction support (requires replica set)
    async def prepare_transaction(self, transaction_id: str):
        """Start MongoDB transaction session"""
        session = await self.client.start_session()
        session.start_transaction(
            write_concern=WriteConcern("majority")
        )
        self._sessions[transaction_id] = session
        
    async def commit_transaction(self, transaction_id: str):
        """Commit MongoDB transaction"""
        session = self._sessions.get(transaction_id)
        if session:
            await session.commit_transaction()
            await session.end_session()
            del self._sessions[transaction_id]
            
    async def rollback_transaction(self, transaction_id: str):
        """Abort MongoDB transaction"""
        session = self._sessions.get(transaction_id)
        if session:
            await session.abort_transaction()
            await session.end_session()
            del self._sessions[transaction_id]
            
    # CRUD operations
    async def insert_one(
        self, 
        collection: str, 
        document: Dict[str, Any],
        transaction_id: Optional[str] = None
    ) -> str:
        """Insert single document"""
        session = self._sessions.get(transaction_id) if transaction_id else None
        coll = self.db[collection]
        result = await coll.insert_one(document, session=session)
        return str(result.inserted_id)
        
    async def insert_many(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        transaction_id: Optional[str] = None
    ) -> List[str]:
        """Insert multiple documents"""
        session = self._sessions.get(transaction_id) if transaction_id else None
        coll = self.db[collection]
        result = await coll.insert_many(documents, session=session)
        return [str(id) for id in result.inserted_ids]
        
    async def find_one(
        self,
        collection: str,
        filter: Dict[str, Any],
        projection: Optional[Dict[str, int]] = None
    ) -> Optional[Dict]:
        """Find single document"""
        coll = self.db[collection]
        doc = await coll.find_one(filter, projection)
        if doc and '_id' in doc:
            doc['_id'] = str(doc['_id'])
        return doc
        
    async def find_many(
        self,
        collection: str,
        filter: Dict[str, Any],
        projection: Optional[Dict[str, int]] = None,
        limit: int = 100,
        skip: int = 0,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict]:
        """Find multiple documents"""
        coll = self.db[collection]
        cursor = coll.find(filter, projection).skip(skip).limit(limit)
        
        if sort:
            cursor = cursor.sort(sort)
            
        docs = await cursor.to_list(length=limit)
        for doc in docs:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        return docs
        
    async def update_one(
        self,
        collection: str,
        filter: Dict[str, Any],
        update: Dict[str, Any],
        transaction_id: Optional[str] = None
    ) -> int:
        """Update single document"""
        session = self._sessions.get(transaction_id) if transaction_id else None
        coll = self.db[collection]
        update_doc = update
        # Allow full Mongo update documents (e.g. {"$set": {...}, "$inc": {...}}).
        # If no operator keys are present, default to $set.
        if not any(str(k).startswith("$") for k in update.keys()):
            update_doc = {"$set": update}

        result = await coll.update_one(filter, update_doc, session=session)
        return result.modified_count
        
    async def delete_one(
        self,
        collection: str,
        filter: Dict[str, Any],
        transaction_id: Optional[str] = None
    ) -> int:
        """Delete single document"""
        session = self._sessions.get(transaction_id) if transaction_id else None
        coll = self.db[collection]
        result = await coll.delete_one(filter, session=session)
        return result.deleted_count