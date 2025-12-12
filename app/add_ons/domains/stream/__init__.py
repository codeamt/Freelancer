"""Demo streams with various access levels"""
from app.add_ons.domains.stream.models.membership import MembershipTier

DEMO_STREAMS = [
    # Free stream
    {
        "id": 1,
        "title": "Welcome to Streaming!",
        "description": "Free introduction to live streaming for everyone",
        "owner_id": 1,
        "owner_name": "Demo Streamer",
        "thumbnail": "https://placehold.co/640x360/10b981/white?text=Free+Stream",
        "is_live": True,
        "viewer_count": 142,
        "visibility": "public",
        "price": 0.00,
        "required_tier": None
    },
    
    # Basic member stream
    {
        "id": 2,
        "title": "Basic Coding Tutorial",
        "description": "Learn Python basics - Basic tier and above",
        "owner_id": 2,
        "owner_name": "Tech Teacher",
        "thumbnail": "https://placehold.co/640x360/3b82f6/white?text=Basic+Member",
        "is_live": False,
        "viewer_count": 0,
        "visibility": "member",
        "price": 0.00,
        "required_tier": MembershipTier.BASIC
    },
    
    # Premium member stream
    {
        "id": 3,
        "title": "Advanced WebRTC Deep Dive",
        "description": "Premium content for serious developers",
        "owner_id": 2,
        "owner_name": "Tech Teacher",
        "thumbnail": "https://placehold.co/640x360/8b5cf6/white?text=Premium+Only",
        "is_live": True,
        "viewer_count": 67,
        "visibility": "member",
        "price": 0.00,
        "required_tier": MembershipTier.PREMIUM
    },
    
    # VIP exclusive
    {
        "id": 4,
        "title": "VIP 1-on-1 Session Recording",
        "description": "Exclusive content for VIP members only",
        "owner_id": 2,
        "owner_name": "Tech Teacher",
        "thumbnail": "https://placehold.co/640x360/f59e0b/white?text=VIP+Exclusive",
        "is_live": False,
        "viewer_count": 0,
        "visibility": "member",
        "price": 0.00,
        "required_tier": MembershipTier.VIP
    },
    
    # Pay-per-view
    {
        "id": 5,
        "title": "Complete Web Development Course",
        "description": "10-hour comprehensive course - one-time purchase",
        "owner_id": 1,
        "owner_name": "Demo Streamer",
        "thumbnail": "https://placehold.co/640x360/ef4444/white?text=Buy+Now",
        "is_live": False,
        "viewer_count": 0,
        "visibility": "paid",
        "price": 49.99,
        "required_tier": None
    },
]