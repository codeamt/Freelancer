"""Stream routes initialization"""
from fasthtml.common import APIRouter

from .streams import router_streams
from .membership import router_membership

router_stream = APIRouter()
router_stream.routes.extend(router_streams.routes)
router_stream.routes.extend(router_membership.routes)


__all__ = ["router_stream", "router_streams", "router_membership", "get_stream_routers"]


def get_stream_routers():
    """Get all stream routers for registration"""
    return [router_streams, router_membership]