"""Stream routes initialization"""
from .streams import router_streams

# Export all routers
__all__ = ['router_streams']


def get_stream_routers():
    """Get all stream routers for registration"""
    return [router_streams]