"""
Dependency Injection Utilities

Provides FastAPI Depends functions for type-safe dependency injection using app.state.
Replaces global singleton pattern with proper dependency injection.
"""
from typing import Optional
from fastapi import Request, Depends
from starlette.requests import Request as StarletteRequest

from core.utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Core Dependencies
# =============================================================================

def get_settings(request: Request):
    """
    Get Settings instance from app.state.
    
    Usage:
        @router.get("/config")
        async def get_config(settings: Settings = Depends(get_settings)):
            return {"env": settings.environment}
    """
    if not hasattr(request.app.state, 'settings'):
        raise RuntimeError("Settings not initialized in app.state")
    return request.app.state.settings


def get_db_service(request: Request):
    """
    Get DBService instance from app.state.
    
    Usage:
        @router.post("/users")
        async def create_user(
            data: dict,
            db: DBService = Depends(get_db_service)
        ):
            return await db.insert("users", data)
    """
    if not hasattr(request.app.state, 'db_service'):
        raise RuntimeError("DBService not initialized in app.state")
    return request.app.state.db_service


def get_session_manager(request: Request):
    """
    Get SessionManager instance from app.state.
    
    Usage:
        @router.get("/session")
        async def get_session(
            session_mgr: SessionManager = Depends(get_session_manager)
        ):
            return await session_mgr.get_session(token)
    """
    if not hasattr(request.app.state, 'session_manager'):
        raise RuntimeError("SessionManager not initialized in app.state")
    return request.app.state.session_manager


def get_settings_service(request: Request):
    """
    Get SettingsService instance from app.state.
    
    Usage:
        @router.get("/settings/{key}")
        async def get_setting(
            key: str,
            settings_svc: SettingsService = Depends(get_settings_service)
        ):
            return await settings_svc.get(key)
    """
    if not hasattr(request.app.state, 'settings_service'):
        raise RuntimeError("SettingsService not initialized in app.state")
    return request.app.state.settings_service


def get_pool_manager(request: Request):
    """
    Get ConnectionPoolManager instance from app.state.
    
    Usage:
        @router.get("/pools/status")
        async def pool_status(
            pool_mgr: ConnectionPoolManager = Depends(get_pool_manager)
        ):
            return pool_mgr.get_pool_stats()
    """
    if not hasattr(request.app.state, 'pool_manager'):
        raise RuntimeError("ConnectionPoolManager not initialized in app.state")
    return request.app.state.pool_manager


# =============================================================================
# Service Dependencies
# =============================================================================

def get_auth_service(request: Request):
    """
    Get AuthService instance from app.state.
    
    Usage:
        @router.post("/auth/login")
        async def login(
            credentials: LoginRequest,
            auth: AuthService = Depends(get_auth_service)
        ):
            return await auth.login(credentials)
    """
    if not hasattr(request.app.state, 'auth_service'):
        raise RuntimeError("AuthService not initialized in app.state")
    return request.app.state.auth_service


def get_user_service(request: Request):
    """
    Get UserService instance from app.state.
    
    Usage:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: str,
            user_svc: UserService = Depends(get_user_service)
        ):
            return await user_svc.get_user(user_id)
    """
    if not hasattr(request.app.state, 'user_service'):
        raise RuntimeError("UserService not initialized in app.state")
    return request.app.state.user_service


def get_storage_service(request: Request):
    """
    Get StorageService instance from app.state.
    
    Usage:
        @router.post("/upload")
        async def upload_file(
            file: UploadFile,
            storage: StorageService = Depends(get_storage_service)
        ):
            return await storage.upload_domain_file(...)
    """
    if not hasattr(request.app.state, 'storage_service'):
        raise RuntimeError("StorageService not initialized in app.state")
    return request.app.state.storage_service


# =============================================================================
# Integration Dependencies
# =============================================================================

def get_ai_client(request: Request):
    """
    Get HuggingFaceClient instance from app.state.
    
    Usage:
        @router.post("/ai/generate")
        async def generate_text(
            prompt: TextGenerationRequest,
            ai: HuggingFaceClient = Depends(get_ai_client)
        ):
            return await ai.generate_text(prompt)
    """
    if not hasattr(request.app.state, 'ai_client'):
        raise RuntimeError("HuggingFaceClient not initialized in app.state")
    return request.app.state.ai_client


def get_addon_loader(request: Request):
    """
    Get AddonLoader instance from app.state.
    
    Usage:
        @router.get("/addons")
        async def list_addons(
            loader: AddonLoader = Depends(get_addon_loader)
        ):
            return loader.get_loaded_addons()
    """
    if not hasattr(request.app.state, 'addon_loader'):
        raise RuntimeError("AddonLoader not initialized in app.state")
    return request.app.state.addon_loader


def get_graphql_service(request: Request):
    """
    Get GraphQLService instance from app.state.
    
    Usage:
        @router.post("/graphql")
        async def graphql_endpoint(
            query: str,
            graphql: GraphQLService = Depends(get_graphql_service)
        ):
            return await graphql.execute(query)
    """
    if not hasattr(request.app.state, 'graphql_service'):
        raise RuntimeError("GraphQLService not initialized in app.state")
    return request.app.state.graphql_service


def get_event_bus(request: Request):
    """
    Get EventBus instance from app.state.
    
    Usage:
        @router.post("/events/publish")
        async def publish_event(
            event: dict,
            bus: EventBus = Depends(get_event_bus)
        ):
            await bus.publish("channel", event)
    """
    if not hasattr(request.app.state, 'event_bus'):
        raise RuntimeError("EventBus not initialized in app.state")
    return request.app.state.event_bus


def get_state_persister(request: Request):
    """
    Get StatePersister instance from app.state.
    
    Usage:
        @router.get("/state/{key}")
        async def get_state(
            key: str,
            persister: StatePersister = Depends(get_state_persister)
        ):
            return await persister.load(key)
    """
    if not hasattr(request.app.state, 'state_persister'):
        raise RuntimeError("StatePersister not initialized in app.state")
    return request.app.state.state_persister


# =============================================================================
# Optional Dependencies (with fallback)
# =============================================================================

def get_settings_optional(request: Request) -> Optional[object]:
    """
    Get Settings instance from app.state, or None if not initialized.
    
    Use this for optional dependencies where the service might not be available.
    """
    return getattr(request.app.state, 'settings', None)


def get_db_service_optional(request: Request) -> Optional[object]:
    """Get DBService instance from app.state, or None if not initialized."""
    return getattr(request.app.state, 'db_service', None)


# =============================================================================
# Utility Functions
# =============================================================================

def initialize_app_state(app, **services):
    """
    Initialize app.state with services.
    
    Usage in app.py:
        from core.di.dependencies import initialize_app_state
        
        initialize_app_state(
            app,
            settings=settings,
            db_service=db_service,
            auth_service=auth_service,
            ...
        )
    
    Args:
        app: FastAPI/Starlette app instance
        **services: Service instances to store in app.state
    """
    for name, service in services.items():
        if service is not None:
            setattr(app.state, name, service)
            logger.info(f"Initialized {name} in app.state")
        else:
            logger.warning(f"Skipped {name} - service is None")


def get_app_state_summary(app) -> dict:
    """
    Get summary of all services in app.state.
    
    Useful for debugging and health checks.
    
    Returns:
        Dict with service names and their initialization status
    """
    state_attrs = [attr for attr in dir(app.state) if not attr.startswith('_')]
    return {
        attr: type(getattr(app.state, attr)).__name__
        for attr in state_attrs
    }


# =============================================================================
# Backward Compatibility Helpers
# =============================================================================

class DependencyInjectionHelper:
    """
    Helper class for gradual migration from global singletons to app.state.
    
    Usage:
        # Old code (global singleton)
        db = get_db_service()
        
        # New code (dependency injection)
        db = DependencyInjectionHelper.get_db_service(request)
    """
    
    @staticmethod
    def get_db_service(request: Request):
        """Get DBService from app.state"""
        return get_db_service(request)
    
    @staticmethod
    def get_settings(request: Request):
        """Get Settings from app.state"""
        return get_settings(request)
    
    @staticmethod
    def get_auth_service(request: Request):
        """Get AuthService from app.state"""
        return get_auth_service(request)


# Export commonly used dependencies
__all__ = [
    # Core
    'get_settings',
    'get_db_service',
    'get_session_manager',
    'get_settings_service',
    'get_pool_manager',
    
    # Services
    'get_auth_service',
    'get_user_service',
    'get_storage_service',
    
    # Integrations
    'get_ai_client',
    'get_addon_loader',
    'get_graphql_service',
    'get_event_bus',
    'get_state_persister',
    
    # Optional
    'get_settings_optional',
    'get_db_service_optional',
    
    # Utilities
    'initialize_app_state',
    'get_app_state_summary',
    'DependencyInjectionHelper',
]
