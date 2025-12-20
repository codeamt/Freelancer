"""
Commerce Domain

E-commerce features including product catalog, shopping cart, and checkout.
Requires authentication for cart and purchase operations.

Routes:
- /shop - Product catalog
- /shop/cart - Shopping cart
- /shop/checkout - Checkout & payment

Integrations:
- Auth: User authentication for purchases
- Stripe: Payment processing (via webhooks)
- Storage: Product image uploads
- GraphQL: Product queries & mutations
"""
from .routes import router_commerce

__all__ = ["router_commerce"]
