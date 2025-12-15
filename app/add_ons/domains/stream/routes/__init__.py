"""Stream routes initialization"""
from .streams import router_streams
from .membership import router_membership

# Export all routers
__all__ = ['router_streams', 'router_membership']


def get_stream_routers():
    """Get all stream routers for registration"""
    return [router_streams, router_membership]