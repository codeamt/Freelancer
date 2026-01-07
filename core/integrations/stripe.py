"""
Stripe Integration

Flattened module containing Stripe client and models.
Business logic should use PaymentService from core.services.payment
"""

import os
import stripe
from starlette.exceptions import HTTPException
from core.utils.logger import get_logger
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = get_logger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")


@dataclass
class StripeCheckoutSession:
    """Stripe checkout session model"""
    id: str
    url: str
    customer_email: Optional[str] = None
    amount_cents: Optional[int] = None
    currency: Optional[str] = None
    status: Optional[str] = None


@dataclass
class StripeSubscription:
    """Stripe subscription model"""
    id: str
    customer_id: str
    status: str
    current_period_start: int
    current_period_end: int
    price_id: str


@dataclass
class StripeRefund:
    """Stripe refund model"""
    id: str
    amount_cents: int
    status: str
    reason: Optional[str] = None
    charge_id: Optional[str] = None


class StripeClient:
    """Stripe API client for payment processing"""
    
    @staticmethod
    def create_checkout_session(
        amount_cents: int, 
        currency: str, 
        success_url: str, 
        cancel_url: str,
        customer_email: Optional[str] = None
    ) -> StripeCheckoutSession:
        """Create a Stripe checkout session"""
        try:
            session_data = {
                'payment_method_types': ['card'],
                'mode': 'payment',
                'line_items': [{
                    'price_data': {
                        'currency': currency,
                        'product_data': {'name': 'FastApp Purchase'},
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }],
                'success_url': success_url,
                'cancel_url': cancel_url,
            }
            
            if customer_email:
                session_data['customer_email'] = customer_email
            
            session = stripe.checkout.Session.create(**session_data)
            logger.info(f"Stripe checkout session created: {session.id}")
            
            return StripeCheckoutSession(
                id=session.id,
                url=session.url,
                customer_email=session.get('customer_email'),
                amount_cents=amount_cents,
                currency=currency,
                status=session.get('status', 'open')
            )
        except Exception as e:
            logger.error(f"Stripe session creation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def create_subscription(customer_email: str, price_id: str) -> StripeSubscription:
        """Create a Stripe subscription"""
        try:
            customer = stripe.Customer.create(email=customer_email)
            subscription = stripe.Subscription.create(
                customer=customer.id, 
                items=[{'price': price_id}]
            )
            logger.info(f"Stripe subscription created for {customer_email}")
            
            return StripeSubscription(
                id=subscription.id,
                customer_id=customer.id,
                status=subscription.status,
                current_period_start=subscription.current_period_start,
                current_period_end=subscription.current_period_end,
                price_id=price_id
            )
        except Exception as e:
            logger.error(f"Stripe subscription error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def create_refund(
        payment_intent_id: Optional[str] = None,
        charge_id: Optional[str] = None,
        amount_cents: Optional[int] = None,
        reason: Optional[str] = None
    ) -> StripeRefund:
        """Create a Stripe refund"""
        try:
            refund_data = {}
            
            if payment_intent_id:
                refund_data['payment_intent'] = payment_intent_id
            elif charge_id:
                refund_data['charge'] = charge_id
            else:
                raise ValueError("Either payment_intent_id or charge_id must be provided")
            
            if amount_cents:
                refund_data['amount'] = amount_cents
            
            if reason:
                refund_data['reason'] = reason
            
            refund = stripe.Refund.create(**refund_data)
            logger.info(f"Stripe refund created: {refund.id}")
            
            return StripeRefund(
                id=refund.id,
                amount_cents=refund.amount,
                status=refund.status,
                reason=refund.get('reason'),
                charge_id=refund.get('charge')
            )
        except Exception as e:
            logger.error(f"Stripe refund error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def get_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """Retrieve a payment intent"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            logger.info(f"Retrieved payment intent: {payment_intent_id}")
            return intent
        except Exception as e:
            logger.error(f"Payment intent retrieval error: {e}")
            raise HTTPException(status_code=404, detail="Payment intent not found")

    @staticmethod
    def create_customer(email: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a Stripe customer"""
        try:
            customer_data = {'email': email}
            if name:
                customer_data['name'] = name
            
            customer = stripe.Customer.create(**customer_data)
            logger.info(f"Stripe customer created: {customer.id}")
            return customer
        except Exception as e:
            logger.error(f"Stripe customer creation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def cancel_subscription(subscription_id: str) -> Dict[str, Any]:
        """Cancel a Stripe subscription"""
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            logger.info(f"Stripe subscription cancelled: {subscription_id}")
            return subscription
        except Exception as e:
            logger.error(f"Stripe subscription cancellation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# Convenience functions for backward compatibility
def create_checkout_session(*args, **kwargs) -> StripeCheckoutSession:
    """Convenience function for creating checkout sessions"""
    return StripeClient.create_checkout_session(*args, **kwargs)

def create_subscription(*args, **kwargs) -> StripeSubscription:
    """Convenience function for creating subscriptions"""
    return StripeClient.create_subscription(*args, **kwargs)

def create_refund(*args, **kwargs) -> StripeRefund:
    """Convenience function for creating refunds"""
    return StripeClient.create_refund(*args, **kwargs)


__all__ = [
    'StripeClient',
    'StripeCheckoutSession',
    'StripeSubscription', 
    'StripeRefund',
    'create_checkout_session',
    'create_subscription',
    'create_refund',
]
