# Routes Package Initialization
# Only import routes that still exist in core
from .main import router_main

# Note: auth, admin, ui routes moved to add_ons
# Note: media, webhooks, graphql moved to add_ons for future use

__all__ = ['router_main']