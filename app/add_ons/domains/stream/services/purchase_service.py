"""Pay-per-view purchase service"""
from typing import List, Optional
from datetime import datetime, timedelta
from core.utils.logger import get_logger
from core.services import get_db_service
from app.add_ons.domains.stream.models.purchase import StreamPurchase

logger = get_logger(__name__)


class PurchaseService:
    """Manage PPV purchases"""
    
    def __init__(self, use_db: bool = False):
        """
        Initialize purchase service.
        
        Args:
            use_db: If True, use DBService. If False, use in-memory storage (default)
        """
        self.use_db = use_db
        self.db = get_db_service() if use_db else None
        # Demo mode: in-memory storage
        self.purchases = []
    
    async def has_purchased(self, user_id: int, stream_id: int) -> bool:
        """Check if user has active purchase for stream"""
        if self.use_db:
            purchase_data = await self.db.find_one(
                "stream_purchases",
                {"user_id": user_id, "stream_id": stream_id, "status": "completed"}
            )
            if purchase_data:
                purchase = self._dict_to_purchase(purchase_data)
                return purchase.has_access()
            return False
        
        # Demo mode
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
    
    async def create_purchase(self, user_id: int, stream_id: int, amount: float,
                       rental: bool = False, stripe_payment_intent_id: str = None) -> StreamPurchase:
        """Create PPV purchase"""
        # Rental = 48 hours, lifetime = no expiration
        access_expires_at = None
        if rental:
            access_expires_at = datetime.utcnow() + timedelta(hours=48)
        
        purchase_data = {
            "user_id": user_id,
            "stream_id": stream_id,
            "amount": amount,
            "stripe_payment_intent_id": stripe_payment_intent_id,
            "status": "completed",
            "access_expires_at": access_expires_at
        }
        
        if self.use_db:
            result = await self.db.insert("stream_purchases", purchase_data)
            logger.info(f"Created purchase in DB: user={user_id}, stream={stream_id}, amount=${amount}")
            return self._dict_to_purchase(result)
        
        # Demo mode
        new_id = len(self.purchases) + 1
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
    
    async def get_user_purchases(self, user_id: int) -> List[StreamPurchase]:
        """Get all purchases for user"""
        if self.use_db:
            purchases_data = await self.db.find_many(
                "stream_purchases",
                {"user_id": user_id},
                limit=100
            )
            return [self._dict_to_purchase(p) for p in purchases_data]
        
        # Demo mode
        return [p for p in self.purchases if p.user_id == user_id]
    
    def _dict_to_purchase(self, data: dict) -> StreamPurchase:
        """Convert database dict to StreamPurchase model"""
        return StreamPurchase(
            id=data.get("id"),
            user_id=data["user_id"],
            stream_id=data["stream_id"],
            amount=data["amount"],
            stripe_payment_intent_id=data.get("stripe_payment_intent_id"),
            status=data.get("status", "completed"),
            purchased_at=data.get("purchased_at", data.get("created_at")),
            access_expires_at=data.get("access_expires_at")
        )