"""
Service Registry

Centralized service registry for dependency injection and service management.
Provides a unified way to access and manage core services.
"""

from typing import Dict, Any, Optional, Type, Callable
from functools import lru_cache
import threading
from contextlib import contextmanager

from core.utils.logger import get_logger

logger = get_logger(__name__)


class ServiceRegistry:
    """
    Centralized service registry with lazy initialization and dependency injection.
    
    Features:
    - Lazy service initialization
    - Thread-safe singleton pattern
    - Dependency injection support
    - Service lifecycle management
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._dependencies: Dict[str, list] = {}
        self._lock = threading.Lock()
        self._initializing: set = set()
    
    def register_factory(
        self, 
        name: str, 
        factory: Callable, 
        dependencies: Optional[list] = None
    ) -> None:
        """
        Register a service factory function.
        
        Args:
            name: Service name
            factory: Factory function that creates the service
            dependencies: List of service names this service depends on
        """
        with self._lock:
            self._factories[name] = factory
            self._dependencies[name] = dependencies or []
            logger.debug(f"Registered factory for service: {name}")
    
    def register_instance(self, name: str, instance: Any) -> None:
        """
        Register a service instance directly.
        
        Args:
            name: Service name
            instance: Service instance
        """
        with self._lock:
            self._services[name] = instance
            logger.debug(f"Registered instance for service: {name}")
    
    def get(self, name: str) -> Any:
        """
        Get a service instance, initializing if necessary.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service is not registered
        """
        # Fast path: return existing instance
        if name in self._services:
            return self._services[name]
        
        # Thread-safe initialization
        with self._lock:
            # Double-check after acquiring lock
            if name in self._services:
                return self._services[name]
            
            # Check if we're already initializing (prevent circular dependencies)
            if name in self._initializing:
                raise ValueError(f"Circular dependency detected for service: {name}")
            
            # Initialize the service
            if name not in self._factories:
                raise KeyError(f"Service not registered: {name}")
            
            try:
                self._initializing.add(name)
                
                # Resolve dependencies first
                dependencies = {}
                for dep_name in self._dependencies.get(name, []):
                    dependencies[dep_name] = self.get(dep_name)
                
                # Create service instance
                factory = self._factories[name]
                if dependencies:
                    instance = factory(**dependencies)
                else:
                    instance = factory()
                
                self._services[name] = instance
                logger.debug(f"Initialized service: {name}")
                
                return instance
                
            finally:
                self._initializing.discard(name)
    
    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._factories or name in self._services
    
    def clear(self) -> None:
        """Clear all registered services (useful for testing)."""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._dependencies.clear()
            self._initializing.clear()
            logger.info("Service registry cleared")
    
    @contextmanager
    def override(self, name: str, instance: Any):
        """
        Context manager to temporarily override a service.
        
        Args:
            name: Service name
            instance: Temporary instance
        """
        original = None
        with self._lock:
            original = self._services.get(name)
            self._services[name] = instance
        
        try:
            yield instance
        finally:
            with self._lock:
                if original is None:
                    self._services.pop(name, None)
                else:
                    self._services[name] = original


# Global service registry instance
_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    return _registry


# Convenience functions
def register_service(name: str, factory: Callable, dependencies: Optional[list] = None) -> None:
    """Register a service factory with the global registry."""
    _registry.register_factory(name, factory, dependencies)


def get_service(name: str) -> Any:
    """Get a service from the global registry."""
    return _registry.get(name)


def register_service_instance(name: str, instance: Any) -> None:
    """Register a service instance with the global registry."""
    _registry.register_instance(name, instance)


# Service registration decorators
def service(name: str, dependencies: Optional[list] = None):
    """
    Decorator to register a service factory.
    
    Usage:
        @service("user_service", dependencies=["db_service"])
        def create_user_service(db_service):
            return UserService(db_service)
    """
    def decorator(factory):
        register_service(name, factory, dependencies)
        return factory
    return decorator


def singleton_service(name: str, dependencies: Optional[list] = None):
    """
    Decorator to register a singleton service factory.
    
    Usage:
        @singleton_service("audit_service")
        def create_audit_service():
            return AuditService()
    """
    def decorator(factory):
        @lru_cache(maxsize=1)
        def cached_factory():
            return factory()
        
        register_service(name, cached_factory, dependencies)
        return factory
    return decorator


# Initialize core services
def _initialize_core_services():
    """Initialize core service factories."""
    
    # Audit Service
    @singleton_service("audit_service")
    def create_audit_service():
        from core.services.audit_service import AuditService
        return AuditService()
    
    # DB Service
    @singleton_service("db_service")
    def create_db_service():
        from core.services.db_service import get_db_service
        return get_db_service()
    
    # Notification Service
    @service("notification_service", dependencies=["db_service"])
    def create_notification_service(db_service):
        from core.services.notification_service import NotificationService
        return NotificationService(db_service)
    
    # User Profile Service
    @service("user_profile_service", dependencies=["db_service"])
    def create_user_profile_service(db_service):
        from core.services.user_profile_service import get_profile_service
        return get_profile_service(user_service=None)
    
    logger.info("Core service factories registered")


# Initialize on import
_initialize_core_services()


# Backward compatibility functions
def get_audit_service():
    """Get audit service (backward compatibility)."""
    return get_service("audit_service")


def get_notification_service():
    """Get notification service (backward compatibility)."""
    return get_service("notification_service")


def get_profile_service():
    """Get profile service (backward compatibility)."""
    return get_service("user_profile_service")


def get_db_service():
    """Get database service (backward compatibility)."""
    return get_service("db_service")
