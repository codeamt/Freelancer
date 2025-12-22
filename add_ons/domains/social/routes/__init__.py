from fasthtml.common import APIRouter

from .social_routes import create_social_routes
from .dm_routes import create_dm_routes

# Create the main social router
router_social = APIRouter()

# Initialize all route modules
create_social_routes()
create_dm_routes()


__all__ = ["router_social"]
