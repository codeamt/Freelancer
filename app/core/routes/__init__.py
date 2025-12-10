# Routes Package Initialization
# Only import routes that still exist in core
from .main import router_main
from .editor import router_editor
from .admin_sites import router_admin_sites
from .auth import router_auth
from .settings import router_settings

# Note: auth, admin, ui routes moved to add_ons
# Note: media, webhooks, graphql moved to add_ons for future use

__all__ = ['router_main', 'router_editor', 'router_admin_sites', 'router_auth', 'router_settings']