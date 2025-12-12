"""
Dependency Injection Utilities

Provides helper functions for accessing services from app.state in FastHTML.
Replaces global singleton pattern with proper dependency injection.

FastHTML Pattern:
    In route handlers, access services directly from request.app.state:
    
    @router.get("/endpoint")
    async def endpoint(request: Request):
        db = request.app.state.db_service
        auth = request.app.state.auth_service
        return await db.query(...)

Note: FastHTML does not use FastAPI's Depends() pattern.
"""
from typing import Optional
from starlette.requests import Request

from core.utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Core Dependencies
# =============================================================================

def get_settings(request: Request):
    """
    Get Settings instance from app.state.
    
    Usage (FastHTML):
        @router.get("/config")
        async def get_config(request: Request):
            settings = get_settings(request)
            return {"env": settings.environment}
    
    Or access directly:
        settings = request.app.state.settings
    """
    if not hasattr(request.app.state, 'settings'):
        raise RuntimeError("Settings not initialized in app.state")
    return request.app.state.settings


def get_db_service(request: Request):
    """
    Get DBService instance from app.state.
    
    Usage (FastHTML):
        @router.post("/users")
        async def create_user(request: Request, data: dict):
            db = get_db_service(request)
            return await db.insert("users", data)
    
    Or access directly:
        db = request.app.state.db_service
    """
    if not hasattr(request.app.state, 'db_service'):
        raise RuntimeError("DBService not initialized in app.state")
    return request.app.state.db_service


def get_session_manager(request: Request):
    """
    Get SessionManager instance from app.state.
    
    Usage (FastHTML):
        @router.get("/session")
        async def get_session(request: Request, token: str):
            session_mgr = get_session_manager(request)
            return await session_mgr.get_session(token)
    
    Or access directly:
        session_mgr = request.app.state.session_manager
    """
    if not hasattr(request.app.state, 'session_manager'):
        raise RuntimeError("SessionManager not initialized in app.state")
    return request.app.state.session_manager


def get_settings_service(request: Request):
    """
    Get SettingsService instance from app.state.
    
    Usage (FastHTML):
        @router.get("/settings/{key}")
        async def get_setting(request: Request, key: str):
            settings_svc = get_settings_service(request)
            return await settings_svc.get(key)
    
    Or access directly:
        settings_svc = request.app.state.settings_service
    """
    if not hasattr(request.app.state, 'settings_service'):
        raise RuntimeError("SettingsService not initialized in app.state")
    return request.app.state.settings_service


def get_pool_manager(request: Request):
    """
    Get ConnectionPoolManager instance from app.state.
    
    Usage (FastHTML):
        @router.get("/pools/status")
        async def pool_status(request: Request):
            pool_mgr = get_pool_manager(request)
            return pool_mgr.get_pool_stats()
    
    Or access directly:
        pool_mgr = request.app.state.pool_manager
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
    
    Usage (FastHTML):
        @router.post("/auth/login")
        async def login(request: Request, credentials: LoginRequest):
            auth = get_auth_service(request)
            return await auth.login(credentials)
    
    Or access directly (recommended):
        auth = request.app.state.auth_service
    """
    if not hasattr(request.app.state, 'auth_service'):
        raise RuntimeError("AuthService not initialized in app.state")
    return request.app.state.auth_service


def get_user_service(request: Request):
    """
    Get UserService instance from app.state.
    
    Usage (FastHTML):
        @router.get("/users/{user_id}")
        async def get_user(request: Request, user_id: str):
            user_svc = get_user_service(request)
            return await user_svc.get_user(user_id)
    
    Or access directly:
        user_svc = request.app.state.user_service
    """
    if not hasattr(request.app.state, 'user_service'):
        raise RuntimeError("UserService not initialized in app.state")
    return request.app.state.user_service


def get_storage_service(request: Request):
    """
    Get StorageService instance from app.state.
    
    Usage (FastHTML):
        @router.post("/upload")
        async def upload_file(request: Request, file: UploadFile):
            storage = get_storage_service(request)
            return await storage.upload_domain_file(...)
    
    Or access directly:
        storage = request.app.state.storage_service
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
    
    Usage (FastHTML):
        @router.post("/ai/generate")
        async def generate_text(request: Request, prompt: TextGenerationRequest):
            ai = get_ai_client(request)
            return await ai.generate_text(prompt)
    
    Or access directly:
        ai = request.app.state.ai_client
    """
    if not hasattr(request.app.state, 'ai_client'):
        raise RuntimeError("HuggingFaceClient not initialized in app.state")
    return request.app.state.ai_client


def get_addon_loader(request: Request):
    """
    Get AddonLoader instance from app.state.
    
    Usage (FastHTML):
        @router.get("/addons")
        async def list_addons(request: Request):
            loader = get_addon_loader(request)
            return loader.get_loaded_addons()
    
    Or access directly:
        loader = request.app.state.addon_loader
    """
    if not hasattr(request.app.state, 'addon_loader'):
        raise RuntimeError("AddonLoader not initialized in app.state")
    return request.app.state.addon_loader


def get_graphql_service(request: Request):
    """
    Get GraphQLService instance from app.state.
    
    Usage (FastHTML):
        @router.post("/graphql")
        async def graphql_endpoint(request: Request, query: str):
            graphql = get_graphql_service(request)
            return await graphql.execute(query)
    
    Or access directly:
        graphql = request.app.state.graphql_service
    """
    if not hasattr(request.app.state, 'graphql_service'):
        raise RuntimeError("GraphQLService not initialized in app.state")
    return request.app.state.graphql_service


def get_event_bus(request: Request):
    """
    Get EventBus instance from app.state.
    
    Usage (FastHTML):
        @router.post("/events/publish")
        async def publish_event(request: Request, event: dict):
            bus = get_event_bus(request)
            await bus.publish("channel", event)
    
    Or access directly:
        bus = request.app.state.event_bus
    """
    if not hasattr(request.app.state, 'event_bus'):
        raise RuntimeError("EventBus not initialized in app.state")
    return request.app.state.event_bus


def get_state_persister(request: Request):
    """
    Get StatePersister instance from app.state.
    
    Usage (FastHTML):
        @router.get("/state/{key}")
        async def get_state(request: Request, key: str):
            persister = get_state_persister(request)
            return await persister.load(key)
    
    Or access directly:
        persister = request.app.state.state_persister
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
        app: FastHTML/Starlette app instance
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
