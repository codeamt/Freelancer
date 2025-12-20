"""
Stripe Integration Module

Low-level Stripe API client.
Business logic should use PaymentService from core.services.payment
"""
from core.integrations.stripe.stripe_client import StripeClient

__all__ = [
    'StripeClient',
]
