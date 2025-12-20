"""Pay-per-view purchase models"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class StreamPurchase:
    """One-time purchase for stream access"""
    id: int
    user_id: int
    stream_id: int
    amount: float
    
    # Payment tracking
    stripe_payment_intent_id: Optional[str] = None
    status: str = "pending"  # pending | completed | failed | refunded
    
    # Access control
    access_expires_at: Optional[datetime] = None  # None = lifetime access
    
    # Metadata
    purchased_at: datetime = field(default_factory=datetime.utcnow)
    
    def has_access(self) -> bool:
        """Check if purchase grants current access"""
        if self.status != "completed":
            return False
        
        if self.access_expires_at is None:
            return True  # Lifetime access
        
        return self.access_expires_at > datetime.utcnow()


@dataclass
class StreamAccess:
    """Unified access record (membership or purchase)"""
    user_id: int
    stream_id: int
    access_type: str  # "free" | "membership" | "purchase"
    granted_by: Optional[int] = None  # membership_id or purchase_id
    granted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None