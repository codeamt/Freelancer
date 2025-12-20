"""Membership and subscription models"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum


class MembershipTier(str, Enum):
    """Membership tier levels"""
    FREE = "free"
    BASIC = "basic"      # $4.99/month - Access to basic streams
    PREMIUM = "premium"  # $9.99/month - Access to premium streams
    VIP = "vip"          # $24.99/month - Access to all streams + perks


TIER_PRICES = {
    MembershipTier.FREE: 0.00,
    MembershipTier.BASIC: 4.99,
    MembershipTier.PREMIUM: 9.99,
    MembershipTier.VIP: 24.99
}


@dataclass
class Membership:
    """User membership/subscription"""
    id: int
    user_id: int
    channel_owner_id: int  # Which streamer they're subscribed to
    tier: MembershipTier
    status: str = "active"  # active | canceled | expired | past_due
    
    # Billing
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    current_period_start: datetime = field(default_factory=datetime.utcnow)
    current_period_end: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    canceled_at: Optional[datetime] = None
    
    def is_active(self) -> bool:
        """Check if membership is currently active"""
        return (
            self.status == "active" and 
            self.current_period_end > datetime.utcnow()
        )
    
    def days_remaining(self) -> int:
        """Days remaining in current period"""
        if not self.is_active():
            return 0
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)


@dataclass
class ChannelMembership:
    """Channel membership configuration"""
    id: int
    channel_owner_id: int
    
    # Tier configuration
    enable_basic: bool = True
    enable_premium: bool = True
    enable_vip: bool = True
    
    # Custom pricing (overrides defaults)
    basic_price: Optional[float] = None
    premium_price: Optional[float] = None
    vip_price: Optional[float] = None
    
    # Perks
    basic_perks: list = field(default_factory=lambda: [
        "Access to basic member streams",
        "Member badge in chat"
    ])
    premium_perks: list = field(default_factory=lambda: [
        "Access to premium streams",
        "Early access to recordings",
        "Custom emotes"
    ])
    vip_perks: list = field(default_factory=lambda: [
        "Access to ALL streams",
        "Priority support",
        "Exclusive content",
        "Monthly 1-on-1 session"
    ])
    
    def get_tier_price(self, tier: MembershipTier) -> float:
        """Get price for tier (custom or default)"""
        if tier == MembershipTier.BASIC and self.basic_price:
            return self.basic_price
        elif tier == MembershipTier.PREMIUM and self.premium_price:
            return self.premium_price
        elif tier == MembershipTier.VIP and self.vip_price:
            return self.vip_price
        return TIER_PRICES[tier]