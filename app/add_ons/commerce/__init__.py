"""
Commerce Add-on

Simple one-page shop demonstrating auth integration.
Requires authentication to add items to cart and checkout.
"""
from .routes import router_commerce

__all__ = ["router_commerce"]
