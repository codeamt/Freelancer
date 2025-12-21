"""
Optimized Video Streaming Service with FastHTML

Features:
- Range header parsing for efficient video streaming
- Async generators for yielding video chunks
- aiofiles for async file reads
- Thread-safe camera access
- Proper resource management
"""
import asyncio
import cv2
import threading
import aiofiles
import os
from typing import AsyncGenerator, Optional, Union, Tuple
from contextlib import asynccontextmanager
from fasthtml.common import Request, Response
from starlette.responses import StreamingResponse
from core.utils.logger import get_logger

logger = get_logger(__name__)


class RangeHeaderParser:
    """Parse HTTP Range headers for byte range requests."""
    
    @staticmethod
    def parse_range_header(range_header: str, file_size: int) -> Tuple[int, int]:
        """Parse Range header and return start and end bytes."""
        if not range_header:
            return 0, file_size - 1
            
        # Remove 'bytes=' prefix
        range_spec = range_header.replace('bytes=', '')
        
        # Parse start and end
        if '-' in range_spec:
            start_str, end_str = range_spec.split('-', 1)
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
        else:
            start = int(range_spec)
            end = file_size - 1
            
        # Clamp to file size
        start = max(0, min(start, file_size - 1))
        end = max(start, min(end, file_size - 1))
        
        return start, end


class Camera:
    """Thread-safe camera capture with optimized frame generation."""
    
    def __init__(self, url: Optional[Union[str, int]] = 0) -> None:
        self.cap = cv2.VideoCapture(url)
        self.lock = threading.Lock()
        self._running = True
        
    def get_frame(self) -> bytes:
        """Capture and encode a single frame as JPEG."""
        with self.lock:
            if not self._running or not self.cap.isOpened():
                return b''
            ret, frame = self.cap.read()
            if not ret:
                return b''
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                return b''
            return jpeg.tobytes()

    def release(self) -> None:
        """Release camera resources."""
        with self.lock:
            self._running = False
            if self.cap.isOpened():
                self.cap.release()


class VideoFileStreamer:
    """Async video file streamer with range header support."""
    
    def __init__(self, file_path: str, chunk_size: int = 8192):
        self.file_path = file_path
        self.chunk_size = chunk_size
        
    async def get_file_size(self) -> int:
        """Get file size asynchronously."""
        return os.path.getsize(self.file_path)
    
    async def stream_range(self, start: int, end: int) -> AsyncGenerator[bytes, None]:
        """Stream file content in the specified byte range."""
        async with aiofiles.open(self.file_path, 'rb') as file:
            await file.seek(start)
            remaining = end - start + 1
            
            while remaining > 0:
                chunk_size = min(self.chunk_size, remaining)
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
                remaining -= len(chunk)


class VideoStreamingService:
    """Main streaming service handling both camera and file streaming."""
    
    def __init__(self):
        self.camera = None
        self._camera_lock = threading.Lock()
        
    def initialize_camera(self, url: Optional[Union[str, int]] = 0):
        """Initialize camera with thread safety."""
        with self._camera_lock:
            if self.camera is None:
                self.camera = Camera(url)
                logger.info(f"Camera initialized with URL: {url}")
                
    def release_camera(self):
        """Release camera resources safely."""
        with self._camera_lock:
            if self.camera:
                self.camera.release()
                self.camera = None
                logger.info("Camera resources released")
    
    async def stream_camera_frames(self) -> AsyncGenerator[bytes, None]:
        """Stream camera frames using async generator."""
        if not self.camera:
            raise RuntimeError("Camera not initialized")
            
        try:
            while True:
                frame = self.camera.get_frame()
                if frame:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                else:
                    break
                await asyncio.sleep(0)  # Yield control to event loop
        except (asyncio.CancelledError, GeneratorExit):
            logger.info("Camera frame generation cancelled")
        finally:
            pass
    
    async def stream_video_file(
        self, 
        file_path: str, 
        range_header: Optional[str] = None
    ) -> Tuple[StreamingResponse, dict]:
        """Stream video file with range header support."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")
            
        streamer = VideoFileStreamer(file_path)
        file_size = await streamer.get_file_size()
        
        # Parse range header
        start, end = RangeHeaderParser.parse_range_header(range_header, file_size)
        content_length = end - start + 1
        
        # Prepare headers
        headers = {
            'Content-Length': str(content_length),
            'Accept-Ranges': 'bytes',
            'Content-Range': f'bytes {start}-{end}/{file_size}'
        }
        
        # Create streaming response
        response = StreamingResponse(
            streamer.stream_range(start, end),
            status_code=206 if range_header else 200,
            headers=headers,
            media_type='video/mp4'
        )
        
        logger.info(f"Streaming video file: {file_path} (bytes {start}-{end}/{file_size})")
        return response, headers
    
    async def get_camera_snapshot(self) -> Response:
        """Get a single camera frame as snapshot."""
        if not self.camera:
            raise RuntimeError("Camera not initialized")
            
        frame = self.camera.get_frame()
        if frame:
            return Response(content=frame, media_type="image/jpeg")
        else:
            return Response(status_code=404, content="Camera frame not available.")


# Global streaming service instance
video_streaming_service = VideoStreamingService()


@asynccontextmanager
async def camera_lifespan():
    """Context manager for camera resource management."""
    try:
        video_streaming_service.initialize_camera()
        yield
    except Exception as e:
        logger.error(f"Camera error: {e}")
    finally:
        video_streaming_service.release_camera()


# Utility functions for FastHTML routes
async def get_video_stream():
    """Get camera video stream for FastHTML route."""
    return StreamingResponse(
        video_streaming_service.stream_camera_frames(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


async def get_snapshot():
    """Get camera snapshot for FastHTML route."""
    return await video_streaming_service.get_camera_snapshot()


async def get_video_file_stream(file_path: str, request: Request):
    """Get video file stream with range support for FastHTML route."""
    range_header = request.headers.get('range')
    response, headers = await video_streaming_service.stream_video_file(
        file_path, range_header
    )
    return response
