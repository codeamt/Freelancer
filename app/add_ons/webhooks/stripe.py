"""
Stripe Webhook Handler (Infrastructure)

Receives Stripe webhooks, verifies signatures, and dispatches to domain handlers.
Uses StripeService for webhook verification.
"""

import os
from fasthtml.common import *
from typing import Dict, Callable, Awaitable
from add_ons.services.stripe import StripeService
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Webhook secret from Stripe dashboard
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_test_placeholder")

# Registry of event handlers (domains register their handlers here)
_event_handlers: Dict[str, list[Callable[[dict], Awaitable[None]]]] = {}


# -----------------------------------------------------------------------------
# Event Handler Registry
# -----------------------------------------------------------------------------

def register_stripe_handler(event_type: str, handler: Callable[[dict], Awaitable[None]]):
    """
    Register a domain handler for a specific Stripe event type.
    
    Args:
        event_type: Stripe event type (e.g., "payment_intent.succeeded")
        handler: Async function that handles the event
    
    Usage:
        from add_ons.webhooks.stripe import register_stripe_handler
        
        @register_stripe_handler("payment_intent.succeeded")
        async def handle_payment(event):
            # Domain-specific logic
            pass
    """
    if event_type not in _event_handlers:
        _event_handlers[event_type] = []
    _event_handlers[event_type].append(handler)
    logger.info(f"Registered Stripe handler for: {event_type}")


async def dispatch_event(event: dict):
    """
    Dispatch event to all registered handlers.
    
    Args:
        event: Stripe event object
    """
    event_type = event.get("type")
    handlers = _event_handlers.get(event_type, [])
    
    if not handlers:
        logger.warning(f"No handlers registered for Stripe event: {event_type}")
        return
    
    logger.info(f"Dispatching Stripe event {event_type} to {len(handlers)} handler(s)")
    
    for handler in handlers:
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Handler failed for {event_type}: {e}")
            # Continue to other handlers even if one fails


# -----------------------------------------------------------------------------
# Webhook Endpoint
# -----------------------------------------------------------------------------

router_stripe_webhooks = APIRouter()


@router_stripe_webhooks.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe webhook endpoint.
    
    Flow:
    1. Receive webhook from Stripe
    2. Verify signature using StripeService
    3. Dispatch to registered domain handlers
    4. Return 200 OK to Stripe
    
    Stripe expects a 200 response within 5 seconds.
    """
    try:
        # Get raw body and signature header
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            logger.warning("Missing Stripe signature header")
            return {"error": "Missing signature"}, 400
        
        # Verify webhook signature using StripeService
        try:
            event = StripeService.construct_event(
                payload=payload,
                sig_header=sig_header,
                webhook_secret=STRIPE_WEBHOOK_SECRET
            )
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return {"error": "Invalid signature"}, 400
        
        # Log event
        event_type = event.get("type")
        event_id = event.get("id")
        logger.info(f"Received Stripe webhook: {event_type} (ID: {event_id})")
        
        # Dispatch to domain handlers (async, don't block webhook response)
        # In production, consider using a task queue (Celery, etc.)
        await dispatch_event(event)
        
        # Return 200 OK to Stripe
        return {"status": "success", "event_id": event_id}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        # Still return 200 to prevent Stripe retries for non-signature errors
        return {"status": "error", "message": str(e)}, 200


# -----------------------------------------------------------------------------
# Convenience Functions
# -----------------------------------------------------------------------------

def get_event_data(event: dict) -> dict:
    """
    Extract event data from Stripe event.
    
    Args:
        event: Stripe event object
        
    Returns:
        Event data object
    """
    return event.get("data", {}).get("object", {})


def get_event_type(event: dict) -> str:
    """
    Get event type from Stripe event.
    
    Args:
        event: Stripe event object
        
    Returns:
        Event type string
    """
    return event.get("type", "")


def get_event_id(event: dict) -> str:
    """
    Get event ID from Stripe event.
    
    Args:
        event: Stripe event object
        
    Returns:
        Event ID string
    """
    return event.get("id", "")


# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = [
    "router_stripe_webhooks",
    "register_stripe_handler",
    "dispatch_event",
    "get_event_data",
    "get_event_type",
    "get_event_id",
]
