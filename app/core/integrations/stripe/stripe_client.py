import os
import stripe
from fastapi import HTTPException
from core.utils.logger import get_logger

logger = get_logger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")

class StripeClient:
    @staticmethod
    def create_checkout_session(amount_cents: int, currency: str, success_url: str, cancel_url: str):
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='payment',
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'product_data': {'name': 'FastApp Purchase'},
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
            )
            logger.info(f"Stripe checkout session created: {session.id}")
            return session.url
        except Exception as e:
            logger.error(f"Stripe session creation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def create_subscription(customer_email: str, price_id: str):
        try:
            customer = stripe.Customer.create(email=customer_email)
            subscription = stripe.Subscription.create(customer=customer.id, items=[{'price': price_id}])
            logger.info(f"Stripe subscription created for {customer_email}")
            return subscription
        except Exception as e:
            logger.error(f"Stripe subscription error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def refund(payment_intent_id: str | None = None, charge_id: str | None = None, amount_cents: int | None = None):
        """Issue a full or partial refund. Provide payment_intent_id or charge_id.
        amount_cents (optional) to make a partial refund.
        """
        try:
            kwargs = {}
            if payment_intent_id:
                kwargs["payment_intent"] = payment_intent_id
            elif charge_id:
                kwargs["charge"] = charge_id
            else:
                raise HTTPException(status_code=400, detail="payment_intent_id or charge_id required")

            if amount_cents:
                kwargs["amount"] = amount_cents

            refund = stripe.Refund.create(**kwargs)
            logger.info(f"Refund created: {refund.id} (status={refund.status})")
            return refund
        except Exception as e:
            logger.error(f"Stripe refund error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def construct_event(payload: bytes, sig_header: str | None, webhook_secret: str):
        try:
            return stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid Stripe signature")