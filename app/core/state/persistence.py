"""
State persistence interfaces and implementations.

This module provides persistence for state across sessions.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .state import State
from datetime import datetime
import json


class StatePersister(ABC):
    """
    Base interface for state persistence.
    
    Implementations can save state to databases, files, etc.
    """
    
    @abstractmethod
    async def save(
        self, 
        app_id: str, 
        state: State, 
        partition_key: Optional[str] = None,
        status: str = "completed"
    ) -> bool:
        """
        Save state to persistent storage.
        
        Args:
            app_id: Application identifier
            state: State to save
            partition_key: Optional partition key for multi-tenancy
            status: Status of the state ("completed" or "failed")
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def load(
        self, 
        app_id: str, 
        partition_key: Optional[str] = None,
        sequence_id: Optional[int] = None
    ) -> Optional[State]:
        """
        Load state from persistent storage.
        
        Args:
            app_id: Application identifier
            partition_key: Optional partition key
            sequence_id: Optional specific sequence ID to load
            
        Returns:
            State instance or None if not found
        """
        pass
    
    @abstractmethod
    async def list_app_ids(
        self, 
        partition_key: Optional[str] = None
    ) -> list[str]:
        """
        List all app IDs.
        
        Args:
            partition_key: Optional partition key filter
            
        Returns:
            List of app IDs
        """
        pass
    
    @abstractmethod
    async def delete(
        self, 
        app_id: str, 
        partition_key: Optional[str] = None
    ) -> bool:
        """
        Delete state from storage.
        
        Args:
            app_id: Application identifier
            partition_key: Optional partition key
            
        Returns:
            True if successful
        """
        pass


class InMemoryPersister(StatePersister):
    """
    In-memory state persistence for development/testing.
    
    State is lost when application restarts.
    """
    
    def __init__(self):
        """Initialize in-memory storage."""
        self._storage: Dict[str, Dict[str, Any]] = {}
    
    def _make_key(self, app_id: str, partition_key: Optional[str] = None) -> str:
        """Make storage key."""
        if partition_key:
            return f"{partition_key}:{app_id}"
        return app_id
    
    async def save(
        self, 
        app_id: str, 
        state: State, 
        partition_key: Optional[str] = None,
        status: str = "completed"
    ) -> bool:
        """Save state to memory."""
        key = self._make_key(app_id, partition_key)
        self._storage[key] = {
            "state": state.serialize(),
            "status": status,
            "saved_at": datetime.utcnow().isoformat()
        }
        return True
    
    async def load(
        self, 
        app_id: str, 
        partition_key: Optional[str] = None,
        sequence_id: Optional[int] = None
    ) -> Optional[State]:
        """Load state from memory."""
        key = self._make_key(app_id, partition_key)
        
        if key not in self._storage:
            return None
        
        state_data = self._storage[key]["state"]
        state = State.deserialize(state_data)
        
        # If sequence_id specified, validate it matches
        if sequence_id is not None and state.sequence_id != sequence_id:
            return None
        
        return state
    
    async def list_app_ids(
        self, 
        partition_key: Optional[str] = None
    ) -> list[str]:
        """List all app IDs."""
        if partition_key:
            prefix = f"{partition_key}:"
            return [
                key[len(prefix):] 
                for key in self._storage.keys() 
                if key.startswith(prefix)
            ]
        return list(self._storage.keys())
    
    async def delete(
        self, 
        app_id: str, 
        partition_key: Optional[str] = None
    ) -> bool:
        """Delete state from memory."""
        key = self._make_key(app_id, partition_key)
        if key in self._storage:
            del self._storage[key]
            return True
        return False


class MongoPersister(StatePersister):
    """
    MongoDB-based state persistence.
    
    Stores state in MongoDB for production use.
    """
    
    def __init__(self, db, collection_name: str = "site_states"):
        """
        Initialize MongoDB persister.
        
        Args:
            db: MongoDB database instance
            collection_name: Collection name for storing states
        """
        self.db = db
        self.collection_name = collection_name
    
    async def save(
        self, 
        app_id: str, 
        state: State, 
        partition_key: Optional[str] = None,
        status: str = "completed"
    ) -> bool:
        """Save state to MongoDB."""
        try:
            document = {
                "app_id": app_id,
                "partition_key": partition_key,
                "state": state.serialize(),
                "status": status,
                "saved_at": datetime.utcnow()
            }
            
            # Upsert based on app_id and partition_key
            query = {"app_id": app_id}
            if partition_key:
                query["partition_key"] = partition_key
            
            await self.db.update_one(
                self.collection_name,
                query,
                document,
                upsert=True
            )
            return True
            
        except Exception as e:
            from core.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to save state to MongoDB: {e}")
            return False
    
    async def load(
        self, 
        app_id: str, 
        partition_key: Optional[str] = None,
        sequence_id: Optional[int] = None
    ) -> Optional[State]:
        """Load state from MongoDB."""
        try:
            query = {"app_id": app_id}
            if partition_key:
                query["partition_key"] = partition_key
            
            document = await self.db.find_one(self.collection_name, query)
            
            if not document:
                return None
            
            state = State.deserialize(document["state"])
            
            # Validate sequence_id if specified
            if sequence_id is not None and state.sequence_id != sequence_id:
                return None
            
            return state
            
        except Exception as e:
            from core.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to load state from MongoDB: {e}")
            return None
    
    async def list_app_ids(
        self, 
        partition_key: Optional[str] = None
    ) -> list[str]:
        """List all app IDs from MongoDB."""
        try:
            query = {}
            if partition_key:
                query["partition_key"] = partition_key
            
            documents = await self.db.find(
                self.collection_name, 
                query, 
                projection={"app_id": 1}
            )
            
            return [doc["app_id"] for doc in documents]
            
        except Exception as e:
            from core.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to list app IDs from MongoDB: {e}")
            return []
    
    async def delete(
        self, 
        app_id: str, 
        partition_key: Optional[str] = None
    ) -> bool:
        """Delete state from MongoDB."""
        try:
            query = {"app_id": app_id}
            if partition_key:
                query["partition_key"] = partition_key
            
            result = await self.db.delete_one(self.collection_name, query)
            return result.deleted_count > 0
            
        except Exception as e:
            from core.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to delete state from MongoDB: {e}")
            return False


class FileSystemPersister(StatePersister):
    """
    File system-based state persistence.
    
    Stores state as JSON files on disk.
    """
    
    def __init__(self, base_path: str = "./state_storage"):
        """
        Initialize file system persister.
        
        Args:
            base_path: Base directory for storing state files
        """
        import os
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    def _make_filepath(self, app_id: str, partition_key: Optional[str] = None) -> str:
        """Make file path for state."""
        import os
        if partition_key:
            partition_dir = os.path.join(self.base_path, partition_key)
            os.makedirs(partition_dir, exist_ok=True)
            return os.path.join(partition_dir, f"{app_id}.json")
        return os.path.join(self.base_path, f"{app_id}.json")
    
    async def save(
        self, 
        app_id: str, 
        state: State, 
        partition_key: Optional[str] = None,
        status: str = "completed"
    ) -> bool:
        """Save state to file."""
        try:
            filepath = self._make_filepath(app_id, partition_key)
            
            data = {
                "app_id": app_id,
                "partition_key": partition_key,
                "state": state.serialize(),
                "status": status,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            from core.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to save state to file: {e}")
            return False
    
    async def load(
        self, 
        app_id: str, 
        partition_key: Optional[str] = None,
        sequence_id: Optional[int] = None
    ) -> Optional[State]:
        """Load state from file."""
        try:
            filepath = self._make_filepath(app_id, partition_key)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            state = State.deserialize(data["state"])
            
            # Validate sequence_id if specified
            if sequence_id is not None and state.sequence_id != sequence_id:
                return None
            
            return state
            
        except Exception as e:
            from core.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to load state from file: {e}")
            return None
    
    async def list_app_ids(
        self, 
        partition_key: Optional[str] = None
    ) -> list[str]:
        """List all app IDs from files."""
        try:
            import os
            
            if partition_key:
                search_dir = os.path.join(self.base_path, partition_key)
            else:
                search_dir = self.base_path
            
            if not os.path.exists(search_dir):
                return []
            
            app_ids = []
            for filename in os.listdir(search_dir):
                if filename.endswith('.json'):
                    app_ids.append(filename[:-5])  # Remove .json
            
            return app_ids
            
        except Exception as e:
            from core.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to list app IDs from files: {e}")
            return []
    
    async def delete(
        self, 
        app_id: str, 
        partition_key: Optional[str] = None
    ) -> bool:
        """Delete state file."""
        try:
            import os
            filepath = self._make_filepath(app_id, partition_key)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            
            return False
            
        except Exception as e:
            from core.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to delete state file: {e}")
            return False