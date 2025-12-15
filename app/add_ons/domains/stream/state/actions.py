"""Stream domain actions - encapsulated business logic"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from core.utils.logger import get_logger
from app.add_ons.domains.stream.state.stream_state import (
    StreamState, StreamStatus, MembershipState, MembershipStatus,
    PurchaseState, PurchaseStatus
)

logger = get_logger(__name__)


class Action(ABC):
    """Base action class"""
    
    @abstractmethod
    async def execute(self, state, context: dict, **kwargs) -> Tuple[Any, 'ActionResult']:
        """
        Execute action
        
        Args:
            state: Current state
            context: Execution context (settings, services, integrations)
            **kwargs: Additional parameters
        
        Returns:
            (new_state, ActionResult)
        """
        pass


@dataclass
class ActionResult:
    """Result of action execution"""
    success: bool
    message: str = ""
    errors: List[str] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None


# ============================================================================
# Stream Actions
# ============================================================================

class CreateStreamAction(Action):
    """Create a new stream"""
    
    def __init__(self, owner_id: int, title: str, description: str = "",
                 visibility: str = "public", price: float = 0.00):
        self.owner_id = owner_id
        self.title = title
        self.description = description
        self.visibility = visibility
        self.price = price
    
    async def execute(self, state: Optional[StreamState], context: dict, **kwargs):
        """Create stream with validation"""
        
        # 1. Validate input
        errors = []
        if not self.title or len(self.title) < 3:
            errors.append("Title must be at least 3 characters")
        if self.visibility not in ['public', 'member', 'paid']:
            errors.append("Invalid visibility")
        if self.price < 0:
            errors.append("Price cannot be negative")
        
        if errors:
            return None, ActionResult(False, "Validation failed", errors)
        
        # 2. Create new state
        new_state = StreamState(
            owner_id=self.owner_id,
            title=self.title,
            description=self.description,
            visibility=self.visibility,
            price=self.price,
            status=StreamStatus.DRAFT,
            thumbnail=f"https://placehold.co/640x360/9333ea/white?text={self.title[:20]}"
        )
        
        # 3. Use Unit of Work to persist
        uow = context.get('uow')
        if uow:
            async with uow:
                stream_id = await uow.stream_repo.create(new_state)
                new_state.stream_id = stream_id
                await uow.commit()
        
        # 4. Log event
        analytics = context.get('analytics')
        if analytics:
            analytics.log_event("streaming", "create_stream", self.owner_id, {
                "stream_id": new_state.stream_id,
                "visibility": self.visibility
            })
        
        logger.info(f"Created stream: {new_state.stream_id} - {self.title}")
        
        return new_state, ActionResult(
            True, 
            "Stream created successfully",
            data={"stream_id": new_state.stream_id}
        )


class GoLiveAction(Action):
    """Start broadcasting a stream"""
    
    def __init__(self, stream_id: int, user_id: int):
        self.stream_id = stream_id
        self.user_id = user_id
    
    async def execute(self, state: StreamState, context: dict, **kwargs):
        """Transition stream to live status"""
        
        # 1. Permission check (via context/middleware)
        if state.owner_id != self.user_id:
            return state, ActionResult(False, "Permission denied")
        
        # 2. Validate state transition
        if not state.can_go_live():
            return state, ActionResult(
                False, 
                f"Cannot go live from status: {state.status.value}"
            )
        
        # 3. Update state
        new_state = state
        new_state.status = StreamStatus.LIVE
        new_state.is_live = True
        new_state.started_at = datetime.utcnow()
        new_state.updated_at = datetime.utcnow()
        
        # 4. Persist via UoW
        uow = context.get('uow')
        if uow:
            async with uow:
                await uow.stream_repo.update(new_state)
                await uow.commit()
        
        # 5. Side effects (notifications, webhooks)
        integrations = context.get('integrations')
        settings = context.get('settings')
        
        if integrations and settings and settings.notifications_enabled:
            # Notify subscribers
            await integrations.notification.notify_subscribers(
                channel_owner_id=state.owner_id,
                message=f"{state.title} is now live!"
            )
        
        logger.info(f"Stream {self.stream_id} went live")
        
        return new_state, ActionResult(True, "Stream is now live")


class EndStreamAction(Action):
    """End a live stream"""
    
    def __init__(self, stream_id: int, user_id: int):
        self.stream_id = stream_id
        self.user_id = user_id
    
    async def execute(self, state: StreamState, context: dict, **kwargs):
        """End stream and optionally archive"""
        
        # 1. Permission check
        if state.owner_id != self.user_id:
            return state, ActionResult(False, "Permission denied")
        
        # 2. Validate transition
        if not state.can_end():
            return state, ActionResult(
                False,
                f"Cannot end stream from status: {state.status.value}"
            )
        
        # 3. Update state
        new_state = state
        new_state.status = StreamStatus.ENDED
        new_state.is_live = False
        new_state.ended_at = datetime.utcnow()
        new_state.updated_at = datetime.utcnow()
        
        # 4. Persist
        uow = context.get('uow')
        if uow:
            async with uow:
                await uow.stream_repo.update(new_state)
                await uow.commit()
        
        # 5. Queue archival task (Celery)
        tasks = context.get('tasks')
        settings = context.get('settings')
        
        if tasks and settings and settings.enable_recording:
            await tasks.queue_task('stream.archive', {
                'stream_id': self.stream_id,
                'started_at': state.started_at.isoformat(),
                'ended_at': new_state.ended_at.isoformat()
            })
        
        logger.info(f"Stream {self.stream_id} ended")
        
        return new_state, ActionResult(True, "Stream ended successfully")


# ============================================================================
# Membership Actions
# ============================================================================

class SubscribeToChannelAction(Action):
    """Subscribe to a channel (create membership)"""
    
    def __init__(self, user_id: int, channel_owner_id: int, tier: str):
        self.user_id = user_id
        self.channel_owner_id = channel_owner_id
        self.tier = tier
    
    async def execute(self, state: Optional[MembershipState], context: dict, **kwargs):
        """Create subscription with Stripe + DB transaction"""
        
        # 1. Validate tier
        valid_tiers = ['basic', 'premium', 'vip']
        if self.tier not in valid_tiers:
            return None, ActionResult(False, "Invalid tier", [f"Tier must be one of: {valid_tiers}"])
        
        # 2. Check for existing membership
        uow = context.get('uow')
        if uow:
            async with uow:
                existing = await uow.membership_repo.find_by_user_and_channel(
                    self.user_id, self.channel_owner_id
                )
                if existing and existing.is_active():
                    return existing, ActionResult(False, "Already subscribed to this channel")
        
        # 3. Get pricing
        settings = context.get('settings')
        tier_prices = {'basic': 4.99, 'premium': 9.99, 'vip': 24.99}
        price = tier_prices.get(self.tier, 4.99)
        
        # 4. Create Stripe subscription (CRITICAL: before DB)
        integrations = context.get('integrations')
        stripe_subscription = None
        
        try:
            if integrations and integrations.stripe:
                stripe_subscription = await integrations.stripe.create_subscription(
                    user_id=self.user_id,
                    channel_owner_id=self.channel_owner_id,
                    tier=self.tier,
                    price=price
                )
                
                if not stripe_subscription:
                    return None, ActionResult(False, "Payment processing failed")
        
        except Exception as e:
            logger.error(f"Stripe subscription failed: {e}")
            return None, ActionResult(False, f"Payment error: {str(e)}")
        
        # 5. Create membership state
        new_state = MembershipState(
            user_id=self.user_id,
            channel_owner_id=self.channel_owner_id,
            tier=self.tier,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id=stripe_subscription.get('id') if stripe_subscription else None,
            price=price,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        # 6. Persist to database (with rollback on failure)
        if uow:
            try:
                async with uow:
                    membership_id = await uow.membership_repo.create(new_state)
                    new_state.membership_id = membership_id
                    await uow.commit()
            except Exception as e:
                logger.error(f"Database error, rolling back Stripe subscription: {e}")
                
                # ROLLBACK: Cancel Stripe subscription
                if stripe_subscription and integrations:
                    await integrations.stripe.cancel_subscription(stripe_subscription['id'])
                
                return None, ActionResult(False, "Subscription failed - payment refunded")
        
        # 7. Side effects (email, notifications)
        if integrations and integrations.email:
            await integrations.email.send_welcome_email(
                user_id=self.user_id,
                tier=self.tier,
                channel_owner_id=self.channel_owner_id
            )
        
        logger.info(f"User {self.user_id} subscribed to channel {self.channel_owner_id} at {self.tier} tier")
        
        return new_state, ActionResult(
            True,
            f"Successfully subscribed to {self.tier} tier",
            data={"membership_id": new_state.membership_id}
        )


class CancelMembershipAction(Action):
    """Cancel a membership subscription"""
    
    def __init__(self, membership_id: int, user_id: int):
        self.membership_id = membership_id
        self.user_id = user_id
    
    async def execute(self, state: MembershipState, context: dict, **kwargs):
        """Cancel subscription (access until period end)"""
        
        # 1. Permission check
        if state.user_id != self.user_id:
            return state, ActionResult(False, "Permission denied")
        
        # 2. Validate state
        if state.status == MembershipStatus.CANCELED:
            return state, ActionResult(False, "Already canceled")
        
        # 3. Cancel Stripe subscription
        integrations = context.get('integrations')
        if integrations and state.stripe_subscription_id:
            try:
                await integrations.stripe.cancel_subscription(state.stripe_subscription_id)
            except Exception as e:
                logger.error(f"Failed to cancel Stripe subscription: {e}")
                return state, ActionResult(False, "Failed to cancel payment subscription")
        
        # 4. Update state (keep active until period end)
        new_state = state
        new_state.status = MembershipStatus.CANCELED
        new_state.canceled_at = datetime.utcnow()
        new_state.updated_at = datetime.utcnow()
        
        # 5. Persist
        uow = context.get('uow')
        if uow:
            async with uow:
                await uow.membership_repo.update(new_state)
                await uow.commit()
        
        logger.info(f"Membership {self.membership_id} canceled (access until {state.current_period_end})")
        
        return new_state, ActionResult(
            True,
            f"Membership canceled. Access continues until {state.current_period_end.strftime('%B %d, %Y')}"
        )


# ============================================================================
# Purchase Actions
# ============================================================================

class PurchaseStreamAction(Action):
    """Purchase PPV access to a stream"""
    
    def __init__(self, user_id: int, stream_id: int, amount: float, rental: bool = False):
        self.user_id = user_id
        self.stream_id = stream_id
        self.amount = amount
        self.rental = rental
    
    async def execute(self, state: Optional[PurchaseState], context: dict, **kwargs):
        """Process payment and grant access"""
        
        # 1. Validate amount
        if self.amount <= 0:
            return None, ActionResult(False, "Invalid amount")
        
        # 2. Check for existing purchase
        uow = context.get('uow')
        if uow:
            async with uow:
                existing = await uow.purchase_repo.find_by_user_and_stream(
                    self.user_id, self.stream_id
                )
                if existing and existing.has_access():
                    return existing, ActionResult(False, "Already purchased")
        
        # 3. Create Stripe payment intent
        integrations = context.get('integrations')
        payment_intent = None
        
        try:
            if integrations and integrations.stripe:
                payment_intent = await integrations.stripe.create_payment_intent(
                    user_id=self.user_id,
                    stream_id=self.stream_id,
                    amount=self.amount
                )
                
                if not payment_intent:
                    return None, ActionResult(False, "Payment processing failed")
        
        except Exception as e:
            logger.error(f"Payment intent creation failed: {e}")
            return None, ActionResult(False, f"Payment error: {str(e)}")
        
        # 4. Create purchase state
        access_expires_at = None
        if self.rental:
            access_expires_at = datetime.utcnow() + timedelta(hours=48)
        
        new_state = PurchaseState(
            user_id=self.user_id,
            stream_id=self.stream_id,
            amount=self.amount,
            rental=self.rental,
            status=PurchaseStatus.COMPLETED,
            stripe_payment_intent_id=payment_intent.get('id') if payment_intent else None,
            access_expires_at=access_expires_at
        )
        
        # 5. Persist
        if uow:
            try:
                async with uow:
                    purchase_id = await uow.purchase_repo.create(new_state)
                    new_state.purchase_id = purchase_id
                    await uow.commit()
            except Exception as e:
                logger.error(f"Database error, refunding payment: {e}")
                
                # ROLLBACK: Refund payment
                if payment_intent and integrations:
                    await integrations.stripe.refund_payment(payment_intent['id'])
                
                return None, ActionResult(False, "Purchase failed - payment refunded")
        
        # 6. Side effects
        if integrations and integrations.email:
            await integrations.email.send_purchase_confirmation(
                user_id=self.user_id,
                stream_id=self.stream_id,
                amount=self.amount,
                rental=self.rental
            )
        
        logger.info(f"User {self.user_id} purchased stream {self.stream_id} for ${self.amount}")
        
        return new_state, ActionResult(
            True,
            "Purchase successful" + (" - 48 hours access" if self.rental else " - lifetime access"),
            data={"purchase_id": new_state.purchase_id}
        )