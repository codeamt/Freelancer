"""
State management core - Immutable state container inspired by Burr.

This module provides the State class for managing site state immutably.
"""

from typing import Any, Dict, List, Optional, Set
from copy import deepcopy
from datetime import datetime
import json


class State:
    """
    Immutable state container for site management.
    
    Provides functional state manipulation with tracking of changes.
    All operations return a new State instance.
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None, sequence_id: int = 0):
        """
        Initialize state.
        
        Args:
            data: Initial state data
            sequence_id: Sequence ID for state versioning
        """
        self._data = deepcopy(data) if data else {}
        self._sequence_id = sequence_id
        self._created_at = datetime.utcnow()
        self._private_keys = set()  # Track private keys (start with __)
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key."""
        return self._data.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Get value by key using bracket notation."""
        return self._data[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in state."""
        return key in self._data
    
    def keys(self) -> List[str]:
        """Get all non-private keys."""
        return [k for k in self._data.keys() if not k.startswith("__")]
    
    def items(self):
        """Get all non-private items."""
        return [(k, v) for k, v in self._data.items() if not k.startswith("__")]
    
    def get_all(self) -> Dict[str, Any]:
        """Get all non-private state data."""
        return {k: v for k, v in self._data.items() if not k.startswith("__")}
    
    def update(self, **kwargs) -> "State":
        """
        Create new state with updated values.
        
        Args:
            **kwargs: Key-value pairs to update
            
        Returns:
            New State instance with updates applied
        """
        new_data = deepcopy(self._data)
        new_data.update(kwargs)
        return State(new_data, self._sequence_id + 1)
    
    def append(self, **kwargs) -> "State":
        """
        Append values to lists in state.
        
        Args:
            **kwargs: Key-value pairs where values are appended to lists
            
        Returns:
            New State instance with appended values
        """
        new_data = deepcopy(self._data)
        for key, value in kwargs.items():
            if key not in new_data:
                new_data[key] = []
            if not isinstance(new_data[key], list):
                raise ValueError(f"Cannot append to non-list key: {key}")
            new_data[key].append(value)
        return State(new_data, self._sequence_id + 1)
    
    def increment(self, **kwargs) -> "State":
        """
        Increment numeric values in state.
        
        Args:
            **kwargs: Key-value pairs where values are added to existing values
            
        Returns:
            New State instance with incremented values
        """
        new_data = deepcopy(self._data)
        for key, value in kwargs.items():
            if key not in new_data:
                new_data[key] = 0
            new_data[key] += value
        return State(new_data, self._sequence_id + 1)
    
    def merge(self, key: str, values: Dict[str, Any]) -> "State":
        """
        Merge dictionary values into nested state.
        
        Args:
            key: Key containing dictionary to merge into
            values: Dictionary to merge
            
        Returns:
            New State instance with merged values
        """
        new_data = deepcopy(self._data)
        if key not in new_data:
            new_data[key] = {}
        if not isinstance(new_data[key], dict):
            raise ValueError(f"Cannot merge into non-dict key: {key}")
        new_data[key].update(values)
        return State(new_data, self._sequence_id + 1)
    
    def subset(self, keys: List[str]) -> "State":
        """
        Create new state with only specified keys.
        
        Args:
            keys: List of keys to include
            
        Returns:
            New State instance with subset of data
        """
        new_data = {k: deepcopy(self._data[k]) for k in keys if k in self._data}
        return State(new_data, self._sequence_id)
    
    def wipe(self, keep: Optional[List[str]] = None, delete: Optional[List[str]] = None) -> "State":
        """
        Create new state with keys removed.
        
        Args:
            keep: List of keys to keep (all others removed)
            delete: List of keys to delete (all others kept)
            
        Returns:
            New State instance with keys removed
        """
        if keep and delete:
            raise ValueError("Cannot specify both keep and delete")
        
        new_data = deepcopy(self._data)
        
        if keep:
            new_data = {k: v for k, v in new_data.items() if k in keep or k.startswith("__")}
        elif delete:
            for key in delete:
                new_data.pop(key, None)
        
        return State(new_data, self._sequence_id + 1)
    
    @property
    def sequence_id(self) -> int:
        """Get current sequence ID."""
        return self._sequence_id
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize state to JSON-compatible dictionary.
        
        Returns:
            Dictionary representation of state
        """
        return {
            "data": self._data,
            "sequence_id": self._sequence_id,
            "created_at": self._created_at.isoformat()
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "State":
        """
        Deserialize state from dictionary.
        
        Args:
            data: Serialized state data
            
        Returns:
            State instance
        """
        state = cls(data.get("data"), data.get("sequence_id", 0))
        if "created_at" in data:
            state._created_at = datetime.fromisoformat(data["created_at"])
        return state
    
    def __repr__(self) -> str:
        """String representation of state."""
        keys = list(self.keys())
        return f"State(keys={keys}, sequence_id={self._sequence_id})"


class StateManager:
    """
    Manager for state lifecycle and history.
    
    Tracks state changes and provides state history capabilities.
    """
    
    def __init__(self, initial_state: Optional[State] = None):
        """
        Initialize state manager.
        
        Args:
            initial_state: Initial state (defaults to empty state)
        """
        self._current = initial_state or State()
        self._history: List[State] = [self._current]
        self._max_history = 100  # Configurable history limit
    
    @property
    def current(self) -> State:
        """Get current state."""
        return self._current
    
    def update(self, new_state: State) -> None:
        """
        Update current state and add to history.
        
        Args:
            new_state: New state to set as current
        """
        self._current = new_state
        self._history.append(new_state)
        
        # Trim history if needed
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
    
    def get_history(self, limit: Optional[int] = None) -> List[State]:
        """
        Get state history.
        
        Args:
            limit: Maximum number of states to return (most recent)
            
        Returns:
            List of state instances
        """
        if limit:
            return self._history[-limit:]
        return self._history.copy()
    
    def rollback(self, steps: int = 1) -> State:
        """
        Rollback to previous state.
        
        Args:
            steps: Number of steps to rollback
            
        Returns:
            Previous state
        """
        if steps >= len(self._history):
            raise ValueError(f"Cannot rollback {steps} steps, only {len(self._history)-1} available")
        
        target_state = self._history[-(steps + 1)]
        self._current = target_state
        # Don't remove from history - keeps audit trail
        return self._current
    
    def get_at_sequence(self, sequence_id: int) -> Optional[State]:
        """
        Get state at specific sequence ID.
        
        Args:
            sequence_id: Sequence ID to retrieve
            
        Returns:
            State at sequence ID or None if not found
        """
        for state in reversed(self._history):
            if state.sequence_id == sequence_id:
                return state
        return None