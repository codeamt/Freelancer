"""
Webhooks Add-on (Infrastructure)

Receives and verifies webhooks from external services.
Dispatches events to domain handlers.

Available Webhooks:
- Stripe: Payment events, subscriptions, disputes
- OAuth: Authentication callbacks (future)

Usage:
    # In app.py
    from add_ons.webhooks.stripe import router_stripe_webhooks
    app.mount("/", router_stripe_webhooks)
    
    # In domain
    from add_ons.domains.commerce import stripe_handlers  # Auto-registers handlers
"""

from .stripe import router_stripe_webhooks, register_stripe_handler

__all__ = [
    "router_stripe_webhooks",
    "register_stripe_handler",
]
