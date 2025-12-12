"""Stream domain models - lightweight in-memory for demo mode"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Stream:
    """Stream model"""
    id: int
    owner_id: int
    title: str
    description: str = ""
    thumbnail: str = ""
    is_live: bool = False
    visibility: str = "public"  # public | private | paid
    price: float = 0.00
    viewer_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # YouTube integration fields
    yt_broadcast_id: Optional[str] = None
    yt_stream_id: Optional[str] = None
    yt_ingest_url: Optional[str] = None
    yt_stream_key: Optional[str] = None
    yt_watch_url: Optional[str] = None
    
    # WebRTC fields
    webrtc_room: Optional[str] = None


@dataclass
class ChatMessage:
    """Chat message model"""
    id: int
    stream_id: int
    user_id: int
    username: str
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ViewerSession:
    """Viewer session tracking"""
    id: int
    stream_id: int
    user_id: Optional[int]
    ip_address: str
    joined_at: datetime = field(default_factory=datetime.utcnow)
    left_at: Optional[datetime] = None


@dataclass
class Subscription:
    """Channel subscription"""
    id: int
    channel_owner_id: int
    subscriber_id: int
    tier: str  # "basic" | "premium" | "vip"
    price: float
    subscribed_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None