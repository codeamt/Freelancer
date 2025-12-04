# app/core/db/interfaces/base_repository.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, AsyncIterator, Optional, List, Dict, Any
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseRepository(ABC):
    """Abstract base repository with single and batch operations"""
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """Get single entity by ID"""
        pass

    @abstractmethod 
    async def save(self, entity: T) -> T:
        """Save single entity"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete single entity by ID"""
        pass

    @abstractmethod
    async def get_bulk(self, ids: List[str]) -> Dict[str, T]:
        """Batch get entities by IDs (returns dict by ID)"""
        pass

    @abstractmethod
    async def save_bulk(self, entities: List[T]) -> List[T]:
        """Batch save entities"""
        pass

    @abstractmethod
    async def delete_bulk(self, ids: List[str]) -> int:
        """Batch delete entities (returns count deleted)"""
        pass

    @abstractmethod
    async def update_bulk(self, updates: Dict[str, Dict[str, Any]]) -> int:
        """Batch update entities (returns count updated)"""
        pass

    @abstractmethod
    async def stream_all(self) -> AsyncIterator[T]:
        """Stream all entities"""
        pass