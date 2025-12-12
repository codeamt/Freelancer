"""
Application Factory - DRY helper for creating FastHTML apps with consistent setup.

Eliminates duplicate middleware and security setup across example apps.
"""
from fasthtml.common import *
from monsterui.all import *
from typing import Optional, Callable
from core.middleware.security import (
    SecurityHeaders,
    RateLimitMiddleware,
    SecurityMiddleware
)
from core.utils.logger import get_logger

logger = get_logger(__name__)


def apply_standard_middleware(
    app,
    enable_rate_limiting: bool = True,
    enable_security_headers: bool = True,
    enable_input_sanitization: bool = True,
    rate_limit_per_minute: int = 60
):
    """
    Apply standard middleware to a FastHTML app.
    
    Args:
        app: FastHTML application instance
        enable_rate_limiting: Enable rate limiting middleware
        enable_security_headers: Enable security headers middleware
        enable_input_sanitization: Enable input sanitization
        rate_limit_per_minute: Requests per minute per IP
        
    Returns:
        The app with middleware applied
    """
    if enable_security_headers:
        app.middleware.append(SecurityHeaders())
        logger.debug("✓ Security headers middleware applied")
    
    if enable_rate_limiting:
        app.middleware.append(RateLimitMiddleware(max_requests=rate_limit_per_minute))
        logger.debug(f"✓ Rate limiting middleware applied ({rate_limit_per_minute} req/min)")
    
    if enable_input_sanitization:
        app.middleware.append(SecurityMiddleware())
        logger.debug("✓ Input sanitization middleware applied")
    
    return app


def create_example_app(
    name: str,
    theme=Theme.slate,
    enable_middleware: bool = True,
    rate_limit_per_minute: int = 60,
    custom_headers: Optional[list] = None
) -> FastHTML:
    """
    Factory for creating example apps with consistent setup.
    
    Eliminates duplicate app initialization code across examples.
    
    Args:
        name: Application name for logging
        theme: MonsterUI theme to use
        enable_middleware: Whether to apply standard middleware
        rate_limit_per_minute: Rate limit threshold
        custom_headers: Additional headers to include
        
    Returns:
        Configured FastHTML application
        
    Example:
        >>> app = create_example_app("E-Shop", theme=Theme.violet)
        >>> @app.get("/")
        >>> def home():
        >>>     return Div("Welcome!")
    """
    logger.info(f"Creating {name} app with {theme.__class__.__name__} theme")
    
    # Combine theme headers with custom headers
    headers = [*theme.headers()]
    if custom_headers:
        headers.extend(custom_headers)
    
    # Create FastHTML app
    app = FastHTML(hdrs=headers)
    
    # Apply standard middleware if enabled
    if enable_middleware:
        apply_standard_middleware(
            app,
            enable_rate_limiting=True,
            enable_security_headers=True,
            enable_input_sanitization=True,
            rate_limit_per_minute=rate_limit_per_minute
        )
        logger.debug(f"✓ Standard middleware applied to {name}")
    
    return app


def create_authenticated_app(
    name: str,
    auth_service,
    theme=Theme.slate,
    enable_middleware: bool = True,
    rate_limit_per_minute: int = 60
) -> FastHTML:
    """
    Create an app with authentication support.
    
    Args:
        name: Application name
        auth_service: AuthService instance for authentication
        theme: MonsterUI theme
        enable_middleware: Apply standard middleware
        rate_limit_per_minute: Rate limit threshold
        
    Returns:
        FastHTML app with auth support
    """
    app = create_example_app(
        name=name,
        theme=theme,
        enable_middleware=enable_middleware,
        rate_limit_per_minute=rate_limit_per_minute
    )
    
    # Attach auth service to app state
    app.state.auth_service = auth_service
    logger.debug(f"✓ Auth service attached to {name}")
    
    return app
