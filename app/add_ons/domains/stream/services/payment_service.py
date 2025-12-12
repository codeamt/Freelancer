"""Stripe payment integration for streams"""
import os
from typing import Optional
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Stripe config
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')


class StreamPaymentService:
    """Handle Stripe payments for streams"""
    
    def __init__(self):
        self.stripe_available = bool(STRIPE_SECRET_KEY)
        if self.stripe_available:
            try:
                import stripe
                stripe.api_key = STRIPE_SECRET_KEY
                self.stripe = stripe
            except ImportError:
                logger.warning("Stripe library not installed")
                self.stripe_available = False
    
    def create_subscription(self, user_id: int, channel_owner_id: int, 
                          tier: str, price: float) -> Optional[dict]:
        """Create Stripe subscription"""
        if not self.stripe_available:
            logger.warning("Stripe not configured - using demo mode")
            return {"id": f"sub_demo_{user_id}_{channel_owner_id}"}
        
        try:
            # In real implementation:
            # 1. Get/create Stripe customer
            # 2. Create subscription with price
            # 3. Return subscription object
            
            subscription = self.stripe.Subscription.create(
                customer=f"cus_{user_id}",  # Should get/create real customer
                items=[{"price": price}],
                metadata={
                    "user_id": user_id,
                    "channel_owner_id": channel_owner_id,
                    "tier": tier
                }
            )
            
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end
            }
        
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return None
    
    def create_payment_intent(self, user_id: int, stream_id: int, 
                            amount: float) -> Optional[dict]:
        """Create Stripe payment intent for PPV"""
        if not self.stripe_available:
            logger.warning("Stripe not configured - using demo mode")
            return {
                "id": f"pi_demo_{user_id}_{stream_id}",
                "client_secret": "demo_secret"
            }
        
        try:
            amount_cents = int(amount * 100)
            
            payment_intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                metadata={
                    "user_id": user_id,
                    "stream_id": stream_id,
                    "type": "stream_purchase"
                }
            )
            
            return {
                "id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "status": payment_intent.status
            }
        
        except Exception as e:
            logger.error(f"Failed to create payment intent: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel Stripe subscription"""
        if not self.stripe_available:
            return True
        
        try:
            self.stripe.Subscription.delete(subscription_id)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False