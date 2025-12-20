"""
Payment Service - Unified payment processing

Provides a unified interface for payment operations across all domains.
Supports Stripe with extensibility for other providers.
"""
import os
from typing import Optional, Dict, List, Literal
from decimal import Decimal
import stripe
from core.utils.logger import get_logger

logger = get_logger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PaymentProvider = Literal["stripe"]
PaymentType = Literal["one_time", "subscription", "pay_per_view"]


class PaymentService:
    """
    Unified payment service for all domains.
    
    Handles:
    - One-time payments
    - Subscriptions
    - Pay-per-view purchases
    - Refunds
    - Payment intents
    """
    
    def __init__(self, provider: PaymentProvider = "stripe"):
        self.provider = provider
        self.stripe_available = bool(os.getenv("STRIPE_SECRET_KEY"))
        
        if not self.stripe_available:
            logger.warning("Stripe not configured - payment operations will use demo mode")
    
    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str = "usd",
        success_url: str = None,
        cancel_url: str = None,
        metadata: Optional[Dict] = None,
        line_items: Optional[List[Dict]] = None,
        customer_email: Optional[str] = None,
        mode: str = "payment"
    ) -> Dict:
        """
        Create Stripe checkout session.
        
        Args:
            amount: Amount in dollars (will be converted to cents)
            currency: Currency code
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel
            metadata: Additional metadata
            line_items: Custom line items (overrides amount)
            customer_email: Pre-fill customer email
            mode: 'payment' for one-time, 'subscription' for recurring
            
        Returns:
            Dict with session_id and url
        """
        if not self.stripe_available:
            logger.warning("Demo mode: Returning mock checkout session")
            return {
                "id": "cs_demo_123",
                "url": success_url or "/payment/success"
            }
        
        try:
            amount_cents = int(amount * 100)
            
            session_params = {
                "payment_method_types": ["card"],
                "mode": mode,
                "success_url": success_url or f"{os.getenv('APP_URL', 'http://localhost:8000')}/payment/success",
                "cancel_url": cancel_url or f"{os.getenv('APP_URL', 'http://localhost:8000')}/payment/cancel",
            }
            
            if line_items:
                session_params["line_items"] = line_items
            else:
                session_params["line_items"] = [{
                    "price_data": {
                        "currency": currency,
                        "product_data": {"name": "Purchase"},
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }]
            
            if metadata:
                session_params["metadata"] = metadata
            
            if customer_email:
                session_params["customer_email"] = customer_email
            
            session = stripe.checkout.Session.create(**session_params)
            
            logger.info(f"Checkout session created: {session.id}")
            return {
                "id": session.id,
                "url": session.url
            }
            
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise
    
    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str = "usd",
        metadata: Optional[Dict] = None,
        customer_id: Optional[str] = None
    ) -> Dict:
        """
        Create payment intent for custom payment flows.
        
        Args:
            amount: Amount in dollars
            currency: Currency code
            metadata: Additional metadata
            customer_id: Stripe customer ID
            
        Returns:
            Dict with payment_intent_id and client_secret
        """
        if not self.stripe_available:
            return {
                "id": "pi_demo_123",
                "client_secret": "demo_secret_123"
            }
        
        try:
            amount_cents = int(amount * 100)
            
            params = {
                "amount": amount_cents,
                "currency": currency,
                "automatic_payment_methods": {"enabled": True},
            }
            
            if metadata:
                params["metadata"] = metadata
            
            if customer_id:
                params["customer"] = customer_id
            
            payment_intent = stripe.PaymentIntent.create(**params)
            
            logger.info(f"Payment intent created: {payment_intent.id}")
            return {
                "id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "status": payment_intent.status
            }
            
        except Exception as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise
    
    def create_subscription(
        self,
        customer_email: str,
        price_id: str,
        metadata: Optional[Dict] = None,
        trial_period_days: Optional[int] = None
    ) -> Dict:
        """
        Create subscription.
        
        Args:
            customer_email: Customer email
            price_id: Stripe price ID
            metadata: Additional metadata
            trial_period_days: Trial period in days
            
        Returns:
            Dict with subscription details
        """
        if not self.stripe_available:
            return {
                "id": "sub_demo_123",
                "status": "active",
                "customer_id": "cus_demo_123"
            }
        
        try:
            customer = stripe.Customer.create(email=customer_email)
            
            params = {
                "customer": customer.id,
                "items": [{"price": price_id}],
            }
            
            if metadata:
                params["metadata"] = metadata
            
            if trial_period_days:
                params["trial_period_days"] = trial_period_days
            
            subscription = stripe.Subscription.create(**params)
            
            logger.info(f"Subscription created: {subscription.id} for {customer_email}")
            return {
                "id": subscription.id,
                "status": subscription.status,
                "customer_id": customer.id,
                "current_period_end": subscription.current_period_end
            }
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            raise
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel subscription."""
        if not self.stripe_available:
            return True
        
        try:
            stripe.Subscription.delete(subscription_id)
            logger.info(f"Subscription cancelled: {subscription_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False
    
    def create_refund(
        self,
        payment_intent_id: Optional[str] = None,
        charge_id: Optional[str] = None,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Issue refund.
        
        Args:
            payment_intent_id: Payment intent ID
            charge_id: Charge ID
            amount: Amount to refund (None for full refund)
            reason: Refund reason
            
        Returns:
            Dict with refund details
        """
        if not self.stripe_available:
            return {"id": "re_demo_123", "status": "succeeded"}
        
        try:
            params = {}
            
            if payment_intent_id:
                params["payment_intent"] = payment_intent_id
            elif charge_id:
                params["charge"] = charge_id
            else:
                raise ValueError("payment_intent_id or charge_id required")
            
            if amount:
                params["amount"] = int(amount * 100)
            
            if reason:
                params["reason"] = reason
            
            refund = stripe.Refund.create(**params)
            
            logger.info(f"Refund created: {refund.id}")
            return {
                "id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100 if refund.amount else None
            }
            
        except Exception as e:
            logger.error(f"Failed to create refund: {e}")
            raise
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer details."""
        if not self.stripe_available:
            return None
        
        try:
            customer = stripe.Customer.retrieve(customer_id)
            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name
            }
        except Exception as e:
            logger.error(f"Failed to get customer: {e}")
            return None
    
    def construct_webhook_event(self, payload: bytes, signature: str, webhook_secret: str):
        """
        Verify and construct webhook event.
        
        Args:
            payload: Request body
            signature: Stripe signature header
            webhook_secret: Webhook secret
            
        Returns:
            Stripe event object
        """
        try:
            return stripe.Webhook.construct_event(payload, signature, webhook_secret)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise
