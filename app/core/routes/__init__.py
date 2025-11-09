# Routes Package Initialization
from .auth import router_auth
from .ui import router as router_ui
from .media import router_media
from .admin import router_admin
from .webhooks import router_webhooks
from .graphql import router_graphql
from .main import router_main

__all__ = ['router_auth', 'router_ui', 'router_media', 'router_admin', 'router_webhooks', 'router_graphql', 'router_main']