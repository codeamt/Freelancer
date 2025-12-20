"""Stream domain state definitions"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class StreamStatus(str, Enum):
    """Stream lifecycle states"""
    DRAFT = "draft"           # Created but not live
    SCHEDULED = "scheduled"   # Scheduled for future
    LIVE = "live"            # Currently broadcasting
    ENDED = "ended"          # Broadcast finished
    ARCHIVED = "archived"    # Saved as VOD


class MembershipStatus(str, Enum):
    """Membership lifecycle states"""
    PENDING = "pending"       # Payment initiated
    ACTIVE = "active"        # Subscription active
    CANCELED = "canceled"    # User canceled (access until period end)
    EXPIRED = "expired"      # Period ended
    PAST_DUE = "past_due"    # Payment failed


class PurchaseStatus(str, Enum):
    """Purchase lifecycle states"""
    INITIATED = "initiated"   # Payment started
    PROCESSING = "processing" # Payment processing
    COMPLETED = "completed"   # Payment successful
    FAILED = "failed"        # Payment failed
    REFUNDED = "refunded"    # Refunded


@dataclass
class StreamState:
    """Complete state for a stream"""
    # Identity
    stream_id: Optional[int] = None
    owner_id: Optional[int] = None
    
    # Content
    title: str = ""
    description: str = ""
    thumbnail: str = ""
    
    # Status
    status: StreamStatus = StreamStatus.DRAFT
    visibility: str = "public"
    is_live: bool = False
    
    # Access control
    required_tier: Optional[str] = None
    price: float = 0.00
    
    # Metrics
    viewer_count: int = 0
    total_views: int = 0
    revenue: float = 0.00
    
    # WebRTC/YouTube
    webrtc_room: Optional[str] = None
    yt_broadcast_id: Optional[str] = None
    yt_stream_key: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Validation errors (populated by actions)
    errors: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if state is valid"""
        return len(self.errors) == 0
    
    def can_go_live(self) -> bool:
        """Check if stream can go live"""
        return (
            self.status in [StreamStatus.DRAFT, StreamStatus.SCHEDULED] and
            bool(self.title) and
            self.owner_id is not None
        )
    
    def can_end(self) -> bool:
        """Check if stream can end"""
        return self.status == StreamStatus.LIVE


@dataclass
class MembershipState:
    """Complete state for a membership"""
    # Identity
    membership_id: Optional[int] = None
    user_id: Optional[int] = None
    channel_owner_id: Optional[int] = None
    
    # Subscription
    tier: str = "basic"
    status: MembershipStatus = MembershipStatus.PENDING
    
    # Billing
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    price: float = 0.00
    
    # Periods
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    canceled_at: Optional[datetime] = None
    
    # Validation
    errors: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        return len(self.errors) == 0
    
    def is_active(self) -> bool:
        """Check if membership is currently active"""
        return (
            self.status == MembershipStatus.ACTIVE and
            self.current_period_end and
            self.current_period_end > datetime.utcnow()
        )


@dataclass
class PurchaseState:
    """Complete state for a PPV purchase"""
    # Identity
    purchase_id: Optional[int] = None
    user_id: Optional[int] = None
    stream_id: Optional[int] = None
    
    # Payment
    amount: float = 0.00
    status: PurchaseStatus = PurchaseStatus.INITIATED
    stripe_payment_intent_id: Optional[str] = None
    
    # Access
    rental: bool = False  # True = 48 hours, False = lifetime
    access_expires_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Validation
    errors: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        return len(self.errors) == 0
    
    def has_access(self) -> bool:
        """Check if purchase grants current access"""
        if self.status != PurchaseStatus.COMPLETED:
            return False
        
        if self.access_expires_at is None:
            return True  # Lifetime access
        
        return self.access_expires_at > datetime.utcnow()


@dataclass
class UserStreamContext:
    """User's context when interacting with streams"""
    user_id: int
    username: str
    role: str
    
    # User's memberships (cached)
    memberships: List[int] = field(default_factory=list)  # channel_owner_ids
    
    # User's purchases (cached)
    purchases: List[int] = field(default_factory=list)  # stream_ids
    
    # Current viewing session
    current_stream_id: Optional[int] = None
    joined_at: Optional[datetime] = None