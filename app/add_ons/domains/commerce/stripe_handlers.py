"""
Commerce Domain - Stripe Event Handlers

Handles Stripe webhook events for e-commerce.
Uses StripeService for Stripe API operations (refunds, etc.).
"""

from add_ons.webhooks.stripe import register_stripe_handler, get_event_data
from add_ons.services.stripe import StripeService
from core.utils.logger import get_logger

logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Payment Events
# -----------------------------------------------------------------------------

@register_stripe_handler("payment_intent.succeeded")
async def handle_payment_succeeded(event: dict):
    """
    Handle successful payment.
    
    Business logic:
    - Update order status to "paid"
    - Send confirmation email
    - Update inventory
    - Trigger fulfillment
    """
    data = get_event_data(event)
    payment_intent_id = data.get("id")
    amount = data.get("amount")  # in cents
    currency = data.get("currency")
    customer_email = data.get("receipt_email")
    
    logger.info(f"Payment succeeded: {payment_intent_id} - {amount/100} {currency}")
    
    try:
        # TODO: Get order from metadata
        # order_id = data.get("metadata", {}).get("order_id")
        # order = await db.find_one("orders", {"_id": order_id})
        
        # TODO: Update order status
        # await db.update_one("orders", {"_id": order_id}, {
        #     "status": "paid",
        #     "payment_intent_id": payment_intent_id,
        #     "paid_at": datetime.utcnow()
        # })
        
        # TODO: Send confirmation email
        # await send_order_confirmation_email(customer_email, order)
        
        # TODO: Update inventory
        # for item in order["items"]:
        #     await db.update_one("products", {"_id": item["product_id"]}, {
        #         "$inc": {"stock": -item["quantity"]}
        #     })
        
        # TODO: Trigger fulfillment
        # await trigger_fulfillment(order_id)
        
        logger.info(f"Order processed successfully for payment {payment_intent_id}")
        
    except Exception as e:
        logger.error(f"Failed to process payment {payment_intent_id}: {e}")


@register_stripe_handler("payment_intent.payment_failed")
async def handle_payment_failed(event: dict):
    """
    Handle failed payment.
    
    Business logic:
    - Update order status to "payment_failed"
    - Send failure notification
    - Log failure reason
    """
    data = get_event_data(event)
    payment_intent_id = data.get("id")
    error = data.get("last_payment_error", {})
    error_message = error.get("message", "Unknown error")
    
    logger.warning(f"Payment failed: {payment_intent_id} - {error_message}")
    
    try:
        # TODO: Update order status
        # order_id = data.get("metadata", {}).get("order_id")
        # await db.update_one("orders", {"_id": order_id}, {
        #     "status": "payment_failed",
        #     "error_message": error_message,
        #     "failed_at": datetime.utcnow()
        # })
        
        # TODO: Send failure notification
        # customer_email = data.get("receipt_email")
        # await send_payment_failed_email(customer_email, error_message)
        
        logger.info(f"Payment failure processed for {payment_intent_id}")
        
    except Exception as e:
        logger.error(f"Failed to process payment failure {payment_intent_id}: {e}")


# -----------------------------------------------------------------------------
# Refund Events
# -----------------------------------------------------------------------------

@register_stripe_handler("charge.refunded")
async def handle_refund(event: dict):
    """
    Handle refund.
    
    Business logic:
    - Update order status to "refunded"
    - Restore inventory
    - Send refund confirmation
    """
    data = get_event_data(event)
    charge_id = data.get("id")
    amount_refunded = data.get("amount_refunded")  # in cents
    refunds = data.get("refunds", {}).get("data", [])
    
    logger.info(f"Refund processed: {charge_id} - {amount_refunded/100}")
    
    try:
        # TODO: Get order from charge ID
        # order = await db.find_one("orders", {"charge_id": charge_id})
        
        # TODO: Update order status
        # await db.update_one("orders", {"_id": order["_id"]}, {
        #     "status": "refunded",
        #     "refunded_amount": amount_refunded,
        #     "refunded_at": datetime.utcnow()
        # })
        
        # TODO: Restore inventory
        # for item in order["items"]:
        #     await db.update_one("products", {"_id": item["product_id"]}, {
        #         "$inc": {"stock": item["quantity"]}
        #     })
        
        # TODO: Send refund confirmation
        # await send_refund_confirmation_email(order["customer_email"], amount_refunded)
        
        logger.info(f"Refund processed successfully for charge {charge_id}")
        
    except Exception as e:
        logger.error(f"Failed to process refund {charge_id}: {e}")


# -----------------------------------------------------------------------------
# Dispute Events
# -----------------------------------------------------------------------------

@register_stripe_handler("charge.dispute.created")
async def handle_dispute_created(event: dict):
    """
    Handle dispute/chargeback.
    
    Business logic:
    - Flag order as disputed
    - Notify admin
    - Gather evidence
    """
    data = get_event_data(event)
    dispute_id = data.get("id")
    charge_id = data.get("charge")
    amount = data.get("amount")
    reason = data.get("reason")
    
    logger.warning(f"Dispute created: {dispute_id} - Charge: {charge_id} - Reason: {reason}")
    
    try:
        # TODO: Flag order
        # order = await db.find_one("orders", {"charge_id": charge_id})
        # await db.update_one("orders", {"_id": order["_id"]}, {
        #     "status": "disputed",
        #     "dispute_id": dispute_id,
        #     "dispute_reason": reason,
        #     "disputed_at": datetime.utcnow()
        # })
        
        # TODO: Notify admin
        # await send_dispute_alert_email(admin_email, order, reason)
        
        # TODO: Gather evidence automatically
        # evidence = await gather_dispute_evidence(order)
        # await submit_dispute_evidence(dispute_id, evidence)
        
        logger.info(f"Dispute flagged for charge {charge_id}")
        
    except Exception as e:
        logger.error(f"Failed to process dispute {dispute_id}: {e}")


# -----------------------------------------------------------------------------
# Checkout Events
# -----------------------------------------------------------------------------

@register_stripe_handler("checkout.session.completed")
async def handle_checkout_completed(event: dict):
    """
    Handle completed checkout session.
    
    Business logic:
    - Create order record
    - Link to customer
    - Trigger payment processing
    """
    data = get_event_data(event)
    session_id = data.get("id")
    customer_email = data.get("customer_details", {}).get("email")
    payment_intent = data.get("payment_intent")
    amount_total = data.get("amount_total")  # in cents
    
    logger.info(f"Checkout completed: {session_id} - {amount_total/100}")
    
    try:
        # TODO: Create order from session metadata
        # metadata = data.get("metadata", {})
        # cart_id = metadata.get("cart_id")
        # cart = await db.find_one("carts", {"_id": cart_id})
        
        # TODO: Create order
        # order = await db.insert_one("orders", {
        #     "customer_email": customer_email,
        #     "items": cart["items"],
        #     "total": amount_total,
        #     "payment_intent": payment_intent,
        #     "session_id": session_id,
        #     "status": "processing",
        #     "created_at": datetime.utcnow()
        # })
        
        # TODO: Clear cart
        # await db.delete_one("carts", {"_id": cart_id})
        
        logger.info(f"Order created from checkout session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to process checkout {session_id}: {e}")


# -----------------------------------------------------------------------------
# Helper Functions (Using StripeService)
# -----------------------------------------------------------------------------

async def issue_refund(order_id: str, amount_cents: int = None):
    """
    Issue a refund for an order using StripeService.
    
    Args:
        order_id: Order ID
        amount_cents: Optional partial refund amount
    """
    try:
        # TODO: Get order
        # order = await db.find_one("orders", {"_id": order_id})
        # payment_intent_id = order.get("payment_intent_id")
        
        # Use StripeService to issue refund
        # refund = StripeService.refund(
        #     payment_intent_id=payment_intent_id,
        #     amount_cents=amount_cents
        # )
        
        # logger.info(f"Refund issued for order {order_id}: {refund.id}")
        # return refund
        
        pass
        
    except Exception as e:
        logger.error(f"Failed to issue refund for order {order_id}: {e}")
        raise


# Usage:
# These handlers are automatically registered when this module is imported.
# Import this module in your commerce app to activate the handlers:
#
# from add_ons.domains.commerce import stripe_handlers
