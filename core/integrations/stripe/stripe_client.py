import os
import stripe
from starlette.exceptions import HTTPException
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
    def create_refund(
        payment_intent_id: str | None = None,
        charge_id: str | None = None,
        amount_cents: int | None = None,
        reason: str | None = None,
        metadata: dict | None = None
    ):
        """
        Create a refund for a payment.
        
        Args:
            payment_intent_id: Payment intent ID to refund
            charge_id: Charge ID to refund (alternative to payment_intent_id)
            amount_cents: Amount to refund in cents (None for full refund)
            reason: Refund reason ('duplicate', 'fraudulent', 'requested_by_customer')
            metadata: Additional metadata for the refund
            
        Returns:
            Stripe Refund object
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
            
            if reason:
                kwargs["reason"] = reason
            
            if metadata:
                kwargs["metadata"] = metadata

            refund = stripe.Refund.create(**kwargs)
            logger.info(f"Refund created: {refund.id} (status={refund.status}, amount={refund.amount})")
            return refund
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid refund request: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Stripe refund error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def get_refund(refund_id: str):
        """
        Retrieve refund details.
        
        Args:
            refund_id: Refund ID
            
        Returns:
            Stripe Refund object
        """
        try:
            refund = stripe.Refund.retrieve(refund_id)
            return refund
        except Exception as e:
            logger.error(f"Failed to retrieve refund {refund_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def list_refunds(payment_intent_id: str | None = None, charge_id: str | None = None, limit: int = 10):
        """
        List refunds for a payment intent or charge.
        
        Args:
            payment_intent_id: Filter by payment intent
            charge_id: Filter by charge
            limit: Maximum number of refunds to return
            
        Returns:
            List of Stripe Refund objects
        """
        try:
            kwargs = {"limit": limit}
            if payment_intent_id:
                kwargs["payment_intent"] = payment_intent_id
            elif charge_id:
                kwargs["charge"] = charge_id
            
            refunds = stripe.Refund.list(**kwargs)
            return refunds.data
        except Exception as e:
            logger.error(f"Failed to list refunds: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def cancel_refund(refund_id: str):
        """
        Cancel a pending refund.
        
        Args:
            refund_id: Refund ID to cancel
            
        Returns:
            Stripe Refund object
        """
        try:
            refund = stripe.Refund.cancel(refund_id)
            logger.info(f"Refund cancelled: {refund_id}")
            return refund
        except Exception as e:
            logger.error(f"Failed to cancel refund {refund_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def handle_dispute(dispute_id: str, evidence: dict | None = None):
        """
        Update dispute with evidence.
        
        Args:
            dispute_id: Dispute ID
            evidence: Evidence to submit (e.g., customer_name, product_description, etc.)
            
        Returns:
            Stripe Dispute object
        """
        try:
            kwargs = {}
            if evidence:
                kwargs["evidence"] = evidence
            
            dispute = stripe.Dispute.modify(dispute_id, **kwargs)
            logger.info(f"Dispute updated: {dispute_id}")
            return dispute
        except Exception as e:
            logger.error(f"Failed to update dispute {dispute_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def close_dispute(dispute_id: str):
        """
        Close a dispute (accept the dispute).
        
        Args:
            dispute_id: Dispute ID
            
        Returns:
            Stripe Dispute object
        """
        try:
            dispute = stripe.Dispute.close(dispute_id)
            logger.info(f"Dispute closed: {dispute_id}")
            return dispute
        except Exception as e:
            logger.error(f"Failed to close dispute {dispute_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def get_dispute(dispute_id: str):
        """
        Retrieve dispute details.
        
        Args:
            dispute_id: Dispute ID
            
        Returns:
            Stripe Dispute object
        """
        try:
            dispute = stripe.Dispute.retrieve(dispute_id)
            return dispute
        except Exception as e:
            logger.error(f"Failed to retrieve dispute {dispute_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def list_disputes(status: str | None = None, limit: int = 10):
        """
        List disputes.
        
        Args:
            status: Filter by status ('warning_needs_response', 'warning_under_review', 
                   'warning_closed', 'needs_response', 'under_review', 'charge_refunded', 
                   'won', 'lost')
            limit: Maximum number of disputes to return
            
        Returns:
            List of Stripe Dispute objects
        """
        try:
            kwargs = {"limit": limit}
            if status:
                kwargs["status"] = status
            
            disputes = stripe.Dispute.list(**kwargs)
            return disputes.data
        except Exception as e:
            logger.error(f"Failed to list disputes: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def construct_event(payload: bytes, sig_header: str | None, webhook_secret: str):
        try:
            return stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid Stripe signature")