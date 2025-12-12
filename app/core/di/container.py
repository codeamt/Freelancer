"""
Dependency Injection Container - Stub implementation.

Provides centralized dependency management for services, integrations, and settings.
"""
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from core.services.auth.context import UserContext
    from core.config.settings_facade import SettingsFacade


@dataclass
class ServiceContainer:
    """
    Container for business logic services.
    
    TODO: Populate with actual service instances:
    - auth_service
    - editor_service
    - admin_service
    - cart_service
    etc.
    """
    pass


@dataclass
class IntegrationContainer:
    """
    Container for external integrations.
    
    TODO: Populate with integration clients:
    - stripe_client
    - email_provider
    - analytics_client
    - cdn_client
    - storage_client
    etc.
    """
    pass


@dataclass
class ExecutionContext:
    """
    Complete execution context for state actions.
    
    Bundles all dependencies needed by Actions:
    - UserContext (user, permissions, cookies)
    - SettingsFacade (role-aware configuration)
    - ServiceContainer (business logic)
    - IntegrationContainer (external services)
    
    Usage:
        context = ExecutionContext(
            user_context=user_context,
            settings=settings_facade,
            services=service_container,
            integrations=integration_container
        )
        
        # Pass to action
        result = await action.execute(state, context)
    """
    user_context: 'UserContext'
    settings: 'SettingsFacade'
    services: ServiceContainer
    integrations: IntegrationContainer
    
    def __post_init__(self):
        """Validate all dependencies are provided."""
        if not self.user_context:
            raise ValueError("user_context is required")
        if not self.settings:
            raise ValueError("settings is required")
