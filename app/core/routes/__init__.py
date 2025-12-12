# Routes Package Initialization
# Only import routes that still exist in core
# Route exports
from .main import router_main
from .auth import router_auth
from .admin_sites import router_admin_sites
from .admin_users import router_admin_users
from .profile import router_profile
from .editor import router_editor
from .settings import router_settings
from .oauth import router_oauth

__all__ = [
    'router_main',
    'router_auth',
    'router_admin_sites',
    'router_admin_users',
    'router_profile',
    'router_editor',
    'router_settings',
    'router_oauth',
]