"""Base Database Service - Abstract Base Class"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class BaseDBService(ABC):
    """
    Abstract base class for database services.
    Add-ons can extend this to implement custom database operations
    with their own collections/tables and domain-specific queries.
    """

    @abstractmethod
    async def connect(self):
        """Establish database connection."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close database connection."""
        pass

    # Generic CRUD operations
    @abstractmethod
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """
        Insert a single document.
        
        Args:
            collection: Collection/table name
            document: Document data to insert
            
        Returns:
            ID of inserted document
        """
        pass

    @abstractmethod
    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict]:
        """
        Find a single document.
        
        Args:
            collection: Collection/table name
            query: Query filter
            
        Returns:
            Document data or None if not found
        """
        pass

    @abstractmethod
    async def find_many(
        self, 
        collection: str, 
        query: Dict[str, Any], 
        limit: int = 50,
        skip: int = 0,
        sort: Optional[Dict[str, int]] = None
    ) -> List[Dict]:
        """
        Find multiple documents.
        
        Args:
            collection: Collection/table name
            query: Query filter
            limit: Maximum number of results
            skip: Number of results to skip (pagination)
            sort: Sort specification
            
        Returns:
            List of documents
        """
        pass

    @abstractmethod
    async def update_one(
        self, 
        collection: str, 
        query: Dict[str, Any], 
        data: Dict[str, Any]
    ) -> Optional[Dict]:
        """
        Update a single document.
        
        Args:
            collection: Collection/table name
            query: Query filter to find document
            data: Update data
            
        Returns:
            Updated document or None if not found
        """
        pass

    @abstractmethod
    async def update_many(
        self, 
        collection: str, 
        query: Dict[str, Any], 
        data: Dict[str, Any]
    ) -> int:
        """
        Update multiple documents.
        
        Args:
            collection: Collection/table name
            query: Query filter
            data: Update data
            
        Returns:
            Number of documents updated
        """
        pass

    @abstractmethod
    async def delete_one(self, collection: str, query: Dict[str, Any]) -> int:
        """
        Delete a single document.
        
        Args:
            collection: Collection/table name
            query: Query filter
            
        Returns:
            Number of documents deleted (0 or 1)
        """
        pass

    @abstractmethod
    async def delete_many(self, collection: str, query: Dict[str, Any]) -> int:
        """
        Delete multiple documents.
        
        Args:
            collection: Collection/table name
            query: Query filter
            
        Returns:
            Number of documents deleted
        """
        pass

    @abstractmethod
    async def count(self, collection: str, query: Dict[str, Any]) -> int:
        """
        Count documents matching query.
        
        Args:
            collection: Collection/table name
            query: Query filter
            
        Returns:
            Count of matching documents
        """
        pass

    @abstractmethod
    async def aggregate(self, collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict]:
        """
        Run an aggregation pipeline.
        
        Args:
            collection: Collection/table name
            pipeline: Aggregation pipeline stages
            
        Returns:
            List of aggregation results
        """
        pass

    # Helper methods for common patterns
    def add_timestamps(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add created_at and updated_at timestamps to document.
        
        Args:
            document: Document to add timestamps to
            
        Returns:
            Document with timestamps
        """
        now = datetime.utcnow()
        document["created_at"] = now
        document["updated_at"] = now
        return document

    def update_timestamp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add updated_at timestamp to update data.
        
        Args:
            data: Update data
            
        Returns:
            Data with updated_at timestamp
        """
        data["updated_at"] = datetime.utcnow()
        return data

    @abstractmethod
    def get_collection_name(self, entity: str) -> str:
        """
        Get the full collection/table name for an entity.
        Add-ons can prefix their collections (e.g., 'lms_courses').
        
        Args:
            entity: Entity name (e.g., 'courses', 'users')
            
        Returns:
            Full collection/table name
        """
        pass
