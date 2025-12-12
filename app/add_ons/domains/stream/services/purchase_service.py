"""Pay-per-view purchase service"""
from typing import List, Optional
from datetime import datetime, timedelta
from core.utils.logger import get_logger
from app.add_ons.domains.stream.models.purchase import StreamPurchase

logger = get_logger(__name__)


class PurchaseService:
    """Manage PPV purchases"""
    
    def __init__(self):
        # Demo mode: in-memory storage
        self.purchases = []
    
    def has_purchased(self, user_id: int, stream_id: int) -> bool:
        """Check if user has active purchase for stream"""
        for purchase in self.purchases:
            if (purchase.user_id == user_id and 
                purchase.stream_id == stream_id and
                purchase.has_access()):
                return True
        return False
    
    def get_purchase(self, user_id: int, stream_id: int) -> Optional[StreamPurchase]:
        """Get user's purchase for stream"""
        for purchase in self.purchases:
            if purchase.user_id == user_id and purchase.stream_id == stream_id:
                return purchase
        return None
    
    def create_purchase(self, user_id: int, stream_id: int, amount: float,
                       rental: bool = False, stripe_payment_intent_id: str = None) -> StreamPurchase:
        """Create PPV purchase"""
        new_id = len(self.purchases) + 1
        
        # Rental = 48 hours, lifetime = no expiration
        access_expires_at = None
        if rental:
            access_expires_at = datetime.utcnow() + timedelta(hours=48)
        
        purchase = StreamPurchase(
            id=new_id,
            user_id=user_id,
            stream_id=stream_id,
            amount=amount,
            stripe_payment_intent_id=stripe_payment_intent_id,
            status="completed",
            access_expires_at=access_expires_at
        )
        
        self.purchases.append(purchase)
        logger.info(f"Created purchase: user={user_id}, stream={stream_id}, amount=${amount}")
        return purchase
    
    def get_user_purchases(self, user_id: int) -> List[StreamPurchase]:
        """Get all purchases for user"""
        return [p for p in self.purchases if p.user_id == user_id]