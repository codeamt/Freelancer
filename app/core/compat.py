# app/core/compat.py
import warnings
from importlib import import_module
from typing import Dict, List, Any, Type

def get_repository(engine: str) -> Type:
    """Get repository class with fallback to legacy implementations"""
    try:
        module = import_module(f"add_ons.services.{engine}.repository")
        repo_class = getattr(module, f"{engine.capitalize()}Repository")
        
        # Add backward compatible batch methods if missing
        if not hasattr(repo_class, 'get_bulk'):
            async def fallback_get_bulk(self, ids: List[str]) -> Dict[str, Any]:
                return {id: await self.get(id) for id in ids}
            repo_class.get_bulk = fallback_get_bulk
            
        return repo_class
    except ImportError as e:
        warnings.warn(f"Falling back to legacy repository: {e}", DeprecationWarning)
        return import_module(f"core.services.{engine}_repo").Repository