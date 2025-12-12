"""Stream access control and paywall logic"""
from typing import Optional, Tuple
from core.utils.logger import get_logger
from app.add_ons.domains.stream.models.membership import MembershipTier
from app.add_ons.domains.stream.services.membership_service import MembershipService
from app.add_ons.domains.stream.services.purchase_service import PurchaseService

logger = get_logger(__name__)


class PaywallService:
    """Determine stream access and paywall requirements"""
    
    def __init__(self):
        self.membership_service = MembershipService()
        self.purchase_service = PurchaseService()
    
    def can_access_stream(self, user_id: Optional[int], stream: dict) -> Tuple[bool, str, dict]:
        """
        Check if user can access stream
        
        Returns:
            (has_access: bool, reason: str, paywall_data: dict)
        """
        visibility = stream.get('visibility', 'public')
        owner_id = stream.get('owner_id')
        stream_id = stream.get('id')
        required_tier = stream.get('required_tier', MembershipTier.BASIC)
        price = stream.get('price', 0.00)
        
        # 1. Owner always has access
        if user_id == owner_id:
            return True, "owner", {}
        
        # 2. Free/public streams
        if visibility == 'public' and price == 0:
            return True, "free", {}
        
        # 3. User must be logged in for paid content
        if not user_id:
            return False, "auth_required", {
                "message": "Sign in to access this stream",
                "redirect": f"/auth/login?redirect=/stream/watch/{stream_id}"
            }
        
        # 4. Check membership access
        if visibility == 'member':
            has_membership = self.membership_service.has_membership(
                user_id, owner_id, required_tier
            )
            
            if has_membership:
                return True, "membership", {}
            
            # No membership - show membership paywall
            return False, "membership_required", {
                "type": "membership",
                "required_tier": required_tier.value,
                "channel_owner_id": owner_id,
                "message": f"Subscribe to access this stream",
                "tiers": self._get_tier_options(owner_id, required_tier)
            }
        
        # 5. Check PPV purchase
        if visibility == 'paid' or price > 0:
            has_purchased = self.purchase_service.has_purchased(user_id, stream_id)
            
            if has_purchased:
                return True, "purchased", {}
            
            # No purchase - show PPV paywall
            return False, "payment_required", {
                "type": "ppv",
                "price": price,
                "stream_id": stream_id,
                "message": f"Purchase access for ${price}",
                "options": [
                    {"type": "rental", "price": price, "duration": "48 hours"},
                    {"type": "lifetime", "price": price * 2, "duration": "Lifetime"}
                ]
            }
        
        # Default deny
        return False, "access_denied", {
            "message": "Access denied"
        }
    
    def _get_tier_options(self, channel_owner_id: int, min_tier: MembershipTier) -> list:
        """Get available membership tier options"""
        config = self.membership_service.get_channel_config(channel_owner_id)
        
        tiers = []
        tier_order = [MembershipTier.BASIC, MembershipTier.PREMIUM, MembershipTier.VIP]
        min_index = tier_order.index(min_tier)
        
        for tier in tier_order[min_index:]:
            if tier == MembershipTier.BASIC and not config.enable_basic:
                continue
            if tier == MembershipTier.PREMIUM and not config.enable_premium:
                continue
            if tier == MembershipTier.VIP and not config.enable_vip:
                continue
            
            price = config.get_tier_price(tier)
            perks = getattr(config, f"{tier.value}_perks", [])
            
            tiers.append({
                "tier": tier.value,
                "name": tier.value.title(),
                "price": price,
                "perks": perks,
                "recommended": tier == min_tier
            })
        
        return tiers
    
    def get_access_badge(self, user_id: Optional[int], stream: dict) -> Optional[str]:
        """Get badge/label for user's access level"""
        if not user_id:
            return None
        
        has_access, reason, _ = self.can_access_stream(user_id, stream)
        
        if not has_access:
            return None
        
        if reason == "owner":
            return "👑 Owner"
        elif reason == "membership":
            membership = self.membership_service.get_membership(
                user_id, stream.get('owner_id')
            )
            if membership:
                return f"⭐ {membership.tier.value.title()} Member"
        elif reason == "purchased":
            return "✅ Purchased"
        elif reason == "free":
            return None
        
        return None