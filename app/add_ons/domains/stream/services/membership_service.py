"""Membership management service"""
from typing import List, Optional
from datetime import datetime, timedelta
from core.utils.logger import get_logger
from core.services import get_db_service
from app.add_ons.domains.stream.models.membership import (
    Membership, MembershipTier, ChannelMembership
)

logger = get_logger(__name__)


class MembershipService:
    """Manage user memberships and subscriptions"""
    
    def __init__(self, use_db: bool = False):
        """
        Initialize membership service.
        
        Args:
            use_db: If True, use DBService. If False, use in-memory storage (default)
        """
        self.use_db = use_db
        self.db = get_db_service() if use_db else None
        # Demo mode: in-memory storage
        self.memberships = []
        self.channel_configs = {}
    
    async def get_user_memberships(self, user_id: int) -> List[Membership]:
        """Get all active memberships for user"""
        if self.use_db:
            memberships_data = await self.db.find_documents(
                "memberships",
                {"user_id": user_id, "status": "active"},
                limit=50,
            )
            return [self._dict_to_membership(m) for m in memberships_data]
        
        # Demo mode
        return [
            m for m in self.memberships 
            if m.user_id == user_id and m.is_active()
        ]
    
    async def get_membership(self, user_id: int, channel_owner_id: int) -> Optional[Membership]:
        """Get user's membership to specific channel"""
        if self.use_db:
            membership_data = await self.db.find_document(
                "memberships",
                {"user_id": user_id, "channel_owner_id": channel_owner_id},
            )
            return self._dict_to_membership(membership_data) if membership_data else None
        
        # Demo mode
        for m in self.memberships:
            if m.user_id == user_id and m.channel_owner_id == channel_owner_id:
                return m
        return None

    async def get_membership_by_id(self, membership_id: int) -> Optional[Membership]:
        """Get membership by numeric ID."""
        if self.use_db:
            membership_data = await self.db.find_document(
                "memberships",
                {"id": membership_id},
            )
            return self._dict_to_membership(membership_data) if membership_data else None

        for m in self.memberships:
            if m.id == membership_id:
                return m
        return None
    
    async def has_membership(
        self,
        user_id: int,
        channel_owner_id: int,
        min_tier: MembershipTier = MembershipTier.BASIC,
    ) -> bool:
        """Check if user has active membership at or above tier"""
        membership = await self.get_membership(user_id, channel_owner_id)
        
        if not membership or not membership.is_active():
            return False
        
        # Tier hierarchy: VIP > PREMIUM > BASIC
        tier_order = {
            MembershipTier.BASIC: 1,
            MembershipTier.PREMIUM: 2,
            MembershipTier.VIP: 3
        }
        
        return tier_order.get(membership.tier, 0) >= tier_order.get(min_tier, 0)
    
    async def create_membership(self, user_id: int, channel_owner_id: int, 
                         tier: MembershipTier, stripe_subscription_id: str = None) -> Membership:
        """Create new membership"""
        membership_data = {
            "user_id": user_id,
            "channel_owner_id": channel_owner_id,
            "tier": tier.value if isinstance(tier, MembershipTier) else tier,
            "stripe_subscription_id": stripe_subscription_id,
            "status": "active",
            "current_period_end": datetime.utcnow() + timedelta(days=30)
        }
        
        if self.use_db:
            existing = await self.db.find_documents("memberships", {}, limit=1000)
            new_id = (
                max(
                    (int(m.get("id")) for m in existing if m.get("id") is not None),
                    default=0,
                )
                + 1
            )
            result = await self.db.insert_document(
                "memberships",
                {"id": new_id, **membership_data},
            )
            logger.info(f"Created membership in DB: user={user_id}, channel={channel_owner_id}, tier={tier}")
            return self._dict_to_membership(result)
        
        # Demo mode
        new_id = len(self.memberships) + 1
        membership = Membership(
            id=new_id,
            user_id=user_id,
            channel_owner_id=channel_owner_id,
            tier=tier,
            stripe_subscription_id=stripe_subscription_id,
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        self.memberships.append(membership)
        logger.info(f"Created membership: user={user_id}, channel={channel_owner_id}, tier={tier}")
        return membership
    
    async def cancel_membership(self, membership_id: int) -> bool:
        """Cancel membership (access until period end)"""
        if self.use_db:
            updated = await self.db.update_document(
                "memberships",
                {"id": membership_id},
                {"$set": {"status": "canceled", "canceled_at": datetime.utcnow()}},
            )
            return bool(updated)

        for m in self.memberships:
            if m.id == membership_id:
                m.status = "canceled"
                m.canceled_at = datetime.utcnow()
                logger.info(f"Canceled membership: {membership_id}")
                return True
        return False
    
    def get_channel_config(self, channel_owner_id: int) -> ChannelMembership:
        """Get or create channel membership configuration"""
        if channel_owner_id not in self.channel_configs:
            self.channel_configs[channel_owner_id] = ChannelMembership(
                id=len(self.channel_configs) + 1,
                channel_owner_id=channel_owner_id
            )
        return self.channel_configs[channel_owner_id]
    
    def _dict_to_membership(self, data: dict) -> Membership:
        """Convert database dict to Membership model"""
        return Membership(
            id=int(data.get("id") or 0),
            user_id=data["user_id"],
            channel_owner_id=data["channel_owner_id"],
            tier=MembershipTier(data["tier"]) if isinstance(data["tier"], str) else data["tier"],
            stripe_subscription_id=data.get("stripe_subscription_id"),
            status=data.get("status", "active"),
            current_period_end=data.get("current_period_end"),
            canceled_at=data.get("canceled_at")
        )


# Demo data
DEMO_MEMBERSHIPS = [
    Membership(
        id=1,
        user_id=1,
        channel_owner_id=2,
        tier=MembershipTier.PREMIUM,
        status="active",
        current_period_end=datetime.utcnow() + timedelta(days=20)
    )
]