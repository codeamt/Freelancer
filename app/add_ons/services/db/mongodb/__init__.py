from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os

def get_mongo_repository(collection_name: str) -> MongoDBRepository:
    """Factory function for MongoDB repositories"""
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "fastapp")
    
    client = AsyncIOMotorClient(uri, uuidRepresentation="standard")
    db = client[db_name]
    return MongoDBRepository(db[collection_name])