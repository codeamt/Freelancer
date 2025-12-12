"""Stream business logic service"""
from typing import List, Optional
from core.utils.logger import get_logger
from core.services import get_db_service

logger = get_logger(__name__)


class StreamService:
    """Stream service - business logic for streams"""
    
    def __init__(self, use_db: bool = False):
        """
        Initialize stream service.
        
        Args:
            use_db: If True, use DBService. If False, use demo data (default)
        """
        self.use_db = use_db
        self.db = get_db_service() if use_db else None
    
    async def list_live_streams(self) -> List[dict]:
        """Get all live streams"""
        if self.use_db:
            streams = await self.db.find_many("streams", {"is_live": True}, limit=100)
            logger.info(f"Listed {len(streams)} live streams from database")
            return streams
        
        # Demo mode
        from app.add_ons.domains.stream import DEMO_STREAMS
        live = [s for s in DEMO_STREAMS if s['is_live']]
        logger.info(f"Listed {len(live)} live streams (demo)")
        return live
    
    async def list_all_streams(self) -> List[dict]:
        """Get all streams (live and recorded)"""
        if self.use_db:
            streams = await self.db.find_many("streams", {}, limit=100)
            logger.info(f"Listed {len(streams)} streams from database")
            return streams
        
        # Demo mode
        from app.add_ons.domains.stream import DEMO_STREAMS
        return DEMO_STREAMS
    
    async def get_stream(self, stream_id: int) -> Optional[dict]:
        """Get stream by ID"""
        if self.use_db:
            stream = await self.db.find_one("streams", {"id": stream_id})
            return stream
        
        # Demo mode
        from app.add_ons.domains.stream import DEMO_STREAMS
        for stream in DEMO_STREAMS:
            if stream['id'] == stream_id:
                return stream
        return None
    
    async def create_stream(self, owner_id: int, title: str, description: str = "", 
                     visibility: str = "public", price: float = 0.00) -> dict:
        """Create a new stream"""
        stream_data = {
            "owner_id": owner_id,
            "title": title,
            "description": description,
            "visibility": visibility,
            "price": price,
            "is_live": False,
            "viewer_count": 0,
            "thumbnail_url": "/static/default-thumbnail.jpg"
        }
        
        if self.use_db:
            stream = await self.db.insert("streams", stream_data)
            logger.info(f"Created stream {stream['id']} in database")
            return stream
        
        # Demo mode
        from app.add_ons.domains.stream import DEMO_STREAMS
        new_id = max(s['id'] for s in DEMO_STREAMS) + 1 if DEMO_STREAMS else 1
        stream = {
            "id": new_id,
            **stream_data,
            "viewer_count": 0,
            "thumbnail": f"https://placehold.co/640x360/9333ea/white?text={title[:20]}",
            "owner_name": "User"  # In real app, fetch from user service
        }
        
        DEMO_STREAMS.append(stream)
        logger.info(f"Created stream: {stream['id']} - {title}")
        return stream
    
    def start_stream(self, stream_id: int) -> Optional[dict]:
        """Start a stream (go live)"""
        stream = self.get_stream(stream_id)
        if stream:
            stream['is_live'] = True
            logger.info(f"Started stream: {stream_id}")
        return stream
    
    def stop_stream(self, stream_id: int) -> Optional[dict]:
        """Stop a stream"""
        stream = self.get_stream(stream_id)
        if stream:
            stream['is_live'] = False
            logger.info(f"Stopped stream: {stream_id}")
        return stream
    
    def get_user_streams(self, owner_id: int) -> List[dict]:
        """Get all streams for a user"""
        from app.add_ons.domains.stream import DEMO_STREAMS
        return [s for s in DEMO_STREAMS if s['owner_id'] == owner_id]