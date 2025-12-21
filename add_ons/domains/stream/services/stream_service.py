"""Stream business logic service"""
from typing import List, Optional
from datetime import datetime
from core.utils.logger import get_logger
from core.services import get_db_service
from .video_streaming_service import video_streaming_service

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
        self.video_service = video_streaming_service
    
    async def list_live_streams(self) -> List[dict]:
        """Get all live streams"""
        if self.use_db:
            streams = await self.db.find_documents("streams", {"is_live": True}, limit=100)
            logger.info(f"Listed {len(streams)} live streams from database")
            return streams
        
        # Demo mode
        from add_ons.domains.stream import DEMO_STREAMS
        live = [s for s in DEMO_STREAMS if s['is_live']]
        logger.info(f"Listed {len(live)} live streams (demo)")
        return live
    
    async def list_all_streams(self) -> List[dict]:
        """Get all streams (live and recorded)"""
        if self.use_db:
            streams = await self.db.find_documents("streams", {}, limit=100)
            logger.info(f"Listed {len(streams)} streams from database")
            return streams
        
        # Demo mode
        from add_ons.domains.stream import DEMO_STREAMS
        return DEMO_STREAMS
    
    async def get_stream(self, stream_id: int) -> Optional[dict]:
        """Get stream by ID"""
        if self.use_db:
            return await self.db.find_document("streams", {"id": stream_id})
        
        # Demo mode
        from add_ons.domains.stream import DEMO_STREAMS
        for stream in DEMO_STREAMS:
            if stream['id'] == stream_id:
                return stream
        return None
    
    async def create_stream(
        self,
        owner_id: int,
        title: str,
        description: str = "",
        visibility: str = "public",
        price: float = 0.00,
        scheduled_start: str = "",
    ) -> dict:
        """Create a new stream"""
        now = datetime.utcnow()

        scheduled_dt = None
        if scheduled_start:
            try:
                # datetime-local sends "YYYY-MM-DDTHH:MM" (no timezone)
                scheduled_dt = datetime.fromisoformat(scheduled_start)
            except Exception:
                scheduled_dt = None

        stream_data = {
            "owner_id": owner_id,
            "title": title,
            "description": description,
            "visibility": visibility,
            "price": price,
            "is_live": False,
            "viewer_count": 0,
            "thumbnail": f"https://placehold.co/640x360/9333ea/white?text={title[:20]}",
            "status": "draft",
            "scheduled_start": scheduled_dt,
            "created_at": now,
            "updated_at": now,
        }
        
        if self.use_db:
            existing = await self.db.find_documents("streams", {}, limit=1000)
            new_id = (max((int(s.get("id")) for s in existing if s.get("id") is not None), default=0) + 1)
            stream = await self.db.insert_document("streams", {"id": new_id, **stream_data})
            logger.info(f"Created stream {new_id} in database")
            return stream
        
        # Demo mode
        from add_ons.domains.stream import DEMO_STREAMS
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
    
    async def start_stream(self, stream_id: int) -> Optional[dict]:
        """Start a stream (go live)"""
        if self.use_db:
            updated = await self.db.update_document(
                "streams",
                {"id": stream_id},
                {"$set": {"is_live": True, "status": "live", "updated_at": datetime.utcnow()}},
            )
            if updated:
                logger.info(f"Started stream: {stream_id}")
            return updated

        stream = await self.get_stream(stream_id)
        if stream:
            stream["is_live"] = True
            stream["status"] = "live"
            logger.info(f"Started stream: {stream_id}")
        return stream
    
    async def stop_stream(self, stream_id: int) -> Optional[dict]:
        """Stop a stream"""
        if self.use_db:
            updated = await self.db.update_document(
                "streams",
                {"id": stream_id},
                {"$set": {"is_live": False, "status": "ended", "updated_at": datetime.utcnow()}},
            )
            if updated:
                logger.info(f"Stopped stream: {stream_id}")
            return updated

        stream = await self.get_stream(stream_id)
        if stream:
            stream["is_live"] = False
            stream["status"] = "ended"
            logger.info(f"Stopped stream: {stream_id}")
        return stream
    
    async def get_user_streams(self, owner_id: int) -> List[dict]:
        """Get all streams for a user"""
        if self.use_db:
            return await self.db.find_documents("streams", {"owner_id": owner_id}, limit=200)

        from add_ons.domains.stream import DEMO_STREAMS
        return [s for s in DEMO_STREAMS if s['owner_id'] == owner_id]

    async def get_streams_by_ids(self, stream_ids: List[int]) -> List[dict]:
        """Get streams by numeric IDs."""
        if not stream_ids:
            return []

        if self.use_db:
            return await self.db.find_documents(
                "streams",
                {"id": {"$in": list(stream_ids)}},
                limit=len(stream_ids),
            )

        from add_ons.domains.stream import DEMO_STREAMS
        sset = set(stream_ids)
        return [s for s in DEMO_STREAMS if s.get('id') in sset]
    
    # Video streaming methods
    def initialize_camera(self, camera_url=None):
        """Initialize camera for video streaming."""
        self.video_service.initialize_camera(camera_url or 0)
        logger.info("Camera initialized for streaming service")
    
    def release_camera(self):
        """Release camera resources."""
        self.video_service.release_camera()
        logger.info("Camera resources released")
    
    async def get_camera_stream(self):
        """Get camera video stream."""
        return await self.video_service.stream_camera_frames()
    
    async def get_camera_snapshot(self):
        """Get camera snapshot."""
        return await self.video_service.get_camera_snapshot()
    
    async def stream_video_file(self, file_path: str, range_header: str = None):
        """Stream video file with range header support."""
        return await self.video_service.stream_video_file(file_path, range_header)
    
    def is_camera_available(self) -> bool:
        """Check if camera is initialized and available."""
        return self.video_service.camera is not None