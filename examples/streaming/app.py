"""
Streaming Platform Example Application

Demonstrates proper use of:
- Optimized video streaming with async generators
- Range header parsing for efficient video file streaming
- aiofiles for async file operations
- Thread-safe camera access
- Service layer integration from add_ons/domains/stream
- Dependency injection from parent app
"""
from fasthtml.common import *
from monsterui.all import *
from typing import Optional
import os

from core.utils.logger import get_logger
from core.ui.layout import Layout
from core.services.auth import AuthService, UserService
from core.services.auth.helpers import get_current_user
from core.services.auth.context import set_user_context, UserContext
from core.db.adapters import PostgresAdapter, MongoDBAdapter, RedisAdapter

# Stream domain imports
from add_ons.domains.stream.services.stream_service import StreamService
from add_ons.domains.stream.services.video_streaming_service import video_streaming_service
from add_ons.domains.stream.routes.streams import router_streams

logger = get_logger(__name__)


def create_streaming_app(
    auth_service: AuthService,
    user_service: UserService,
    postgres: PostgresAdapter,
    mongodb: Optional[MongoDBAdapter] = None,
    redis: Optional[RedisAdapter] = None,
    demo: bool = False
) -> FastHTML:
    """
    Create streaming platform example application.
    
    Args:
        auth_service: Injected authentication service
        user_service: Injected user management service
        postgres: PostgreSQL adapter
        mongodb: MongoDB adapter (optional)
        redis: Redis adapter (optional)
        demo: Whether to run in demo mode
        
    Returns:
        FastHTML application instance
    """
    logger.info(f"Initializing Streaming example app (demo={demo})...")
    
    app = FastHTML(hdrs=[*Theme.slate.headers()])
    
    # Store demo flag and services in app state
    app.state.demo = demo
    app.state.auth_service = auth_service
    app.state.user_service = user_service
    app.state.postgres = postgres
    app.state.mongodb = mongodb
    app.state.redis = redis
    
    # Initialize stream service
    use_db = not demo and postgres is not None
    stream_service = StreamService(use_db=use_db)
    app.state.stream_service = stream_service
    
    # Register stream domain routes
    router_streams.to_app(app)
    
    # Initialize camera for demo
    if demo:
        try:
            video_streaming_service.initialize_camera(0)  # Default camera
            logger.info("Camera initialized for streaming demo")
        except Exception as e:
            logger.warning(f"Could not initialize camera: {e}")
    
    # Base path
    BASE = "/streaming-example"
    
    async def get_user_with_context(request: Request):
        """Get current user from request and set context."""
        user = await get_current_user(request, auth_service)
        if user:
            # Set user context for state system using factory
            class SimpleUser:
                def __init__(self, user_dict):
                    self.id = user_dict.get("id") or int(user_dict.get("_id", 0))
                    self.role = user_dict.get("role", "user")
                    self.email = user_dict.get("email", "")
            
            user_obj = SimpleUser(user)
            user_context = UserContext(user_obj, request)
            set_user_context(user_context)
        return user
    
    @app.get("/")
    async def streaming_home(request: Request):
        """Streaming platform home page"""
        user = await get_user_with_context(request)
        
        # Get live streams
        live_streams = await stream_service.list_live_streams()
        
        content = Div(
            # Hero Section
            Div(
                Div(
                    # Icon
                    Div(
                        UkIcon("play-circle", width="120", height="120", cls="text-red-500 mb-8"),
                        cls="flex justify-center"
                    ),
                    
                    # Title
                    H1("📺 Streaming Platform", cls="text-5xl font-bold mb-4 text-center"),
                    P("Watch, Stream, Create", cls="text-2xl text-gray-500 mb-8 text-center"),
                    
                    # Live Demo Badge
                    Div(
                        Span("🔴 Live Demo Active", cls="badge badge-lg badge-success text-lg px-6 py-4"),
                        cls="flex justify-center mb-12"
                    ),
                    
                    # Live Streams Section
                    Div(
                        H2("🎬 Live Streams", cls="text-3xl font-bold mb-8 text-center"),
                        Div(
                            *[Div(
                                H3(stream.get("title", "Untitled Stream"), cls="text-xl font-semibold mb-2"),
                                P(stream.get("description", "No description"), cls="text-gray-600 mb-4"),
                                Div(
                                    Span(f"👁 {stream.get('viewer_count', 0)} viewers", cls="badge badge-primary mr-2"),
                                    Span("🔴 LIVE", cls="badge badge-error"),
                                    cls="flex gap-2 mb-4"
                                ),
                                A("Watch Now", href=f"{BASE}/watch/{stream.get('id')}", cls="btn btn-primary"),
                                cls="p-6 border rounded-lg hover:shadow-lg transition-shadow"
                            ) for stream in live_streams[:6]],  # Show first 6 streams
                            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
                        ),
                    ),
                    
                    # Demo Features
                    Div(
                        H2("🚀 Try Our Features", cls="text-3xl font-bold mb-8 text-center"),
                        Div(
                            # Camera Stream Demo
                            Div(
                                H3("📹 Live Camera Stream", cls="text-xl font-semibold mb-4"),
                                P("Real-time camera feed using async generators and OpenCV", cls="text-gray-600 mb-4"),
                                Div(
                                    Img(src=f"{BASE}/stream/video-stream", alt="Live Camera Stream", 
                                        cls="w-full max-w-2xl mx-auto rounded-lg shadow-lg"),
                                    cls="flex justify-center mb-4"
                                ),
                                Div(
                                    A("📸 Take Snapshot", href=f"{BASE}/stream/video-snapshot", 
                                      cls="btn btn-primary mr-2", target="_blank"),
                                    A("🔄 Refresh", href="#", cls="btn btn-outline", 
                                      onclick="window.location.reload()"),
                                    cls="flex justify-center gap-2"
                                ),
                                cls="mb-8 p-6 bg-gray-50 rounded-lg"
                            ),
                            
                            # Video File Upload Demo
                            Div(
                                H3("🎬 Upload & Stream", cls="text-xl font-semibold mb-4"),
                                P("Upload video files and stream with range header support", cls="text-gray-600 mb-4"),
                                Form(
                                    Input(type="file", accept="video/*", name="video", cls="mb-4"),
                                    Button("Upload & Stream", cls="btn btn-primary"),
                                    method="post",
                                    action=f"{BASE}/stream/video-upload",
                                    enctype="multipart/form-data",
                                    cls="space-y-4"
                                ),
                                cls="mb-8 p-6 bg-gray-50 rounded-lg"
                            ),
                            
                            cls="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12"
                        ),
                    ),
                    
                    # Tech Stack
                    Div(
                        H3("🛠 Technology Stack", cls="text-2xl font-bold mb-6 text-center"),
                        Div(
                            Div("FastHTML", cls="badge badge-primary mr-2 mb-2"),
                            Div("Async Generators", cls="badge badge-secondary mr-2 mb-2"),
                            Div("Range Headers", cls="badge badge-accent mr-2 mb-2"),
                            Div("aiofiles", cls="badge badge-info mr-2 mb-2"),
                            Div("OpenCV", cls="badge badge-success mr-2 mb-2"),
                            Div("Thread Safety", cls="badge badge-warning mr-2 mb-2"),
                            cls="flex flex-wrap justify-center gap-2"
                        ),
                        cls="bg-gray-50 p-6 rounded-lg"
                    ),
                    
                    cls="max-w-6xl mx-auto"
                ),
                cls="py-16"
            )
        )
        
        return Layout(
            content, 
            title="Streaming Platform | FastApp", 
            current_path=f"{BASE}/", 
            user=user, 
            show_auth=True, 
            demo=demo
        )
    
    @app.get("/demo")
    async def streaming_demo(request: Request):
        """Streaming demo page with camera and file upload"""
        user = await get_user_with_context(request)
        
        content = Div(
            # Hero Section
            Div(
                H1("🎬 Live Streaming Demo", cls="text-4xl font-bold mb-4 text-center"),
                P("Experience real-time video streaming with our optimized technology", 
                  cls="text-lg text-gray-600 mb-8 text-center"),
                cls="py-8"
            ),
            
            # Demo Features Grid
            Div(
                Div(
                    # Camera Stream Demo
                    Div(
                        H3("📹 Live Camera Stream", cls="text-xl font-semibold mb-4"),
                        P("Real-time camera feed using async generators and OpenCV", cls="text-gray-600 mb-4"),
                        Div(
                            Img(src=f"{BASE}/stream/video-stream", alt="Live Camera Stream", 
                                cls="w-full rounded-lg shadow-lg"),
                            cls="mb-4"
                        ),
                        Div(
                            A("📸 Take Snapshot", href=f"{BASE}/stream/video-snapshot", 
                              cls="btn btn-primary mr-2", target="_blank"),
                            A("🔄 Refresh", href="#", cls="btn btn-outline", 
                              onclick="window.location.reload()"),
                            cls="flex gap-2"
                        ),
                        cls="p-6 bg-white rounded-lg shadow-lg"
                    ),
                    cls="lg:col-span-2"
                ),
                
                Div(
                    # File Upload Demo
                    Div(
                        H3("🎬 Video File Upload", cls="text-xl font-semibold mb-4"),
                        P("Upload and stream video files with range header support", cls="text-gray-600 mb-4"),
                        Form(
                            Input(type="file", accept="video/*", name="video", cls="mb-4"),
                            Button("Upload & Stream", cls="btn btn-primary"),
                            method="post",
                            action=f"{BASE}/stream/video-upload",
                            enctype="multipart/form-data",
                            cls="space-y-4"
                        ),
                        cls="p-6 bg-white rounded-lg shadow-lg"
                    ),
                    cls="lg:col-span-1"
                ),
                
                cls="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8"
            ),
            
            # Tech Stack Info
            Div(
                H3("🚀 Technology Stack", cls="text-2xl font-bold mb-4"),
                Div(
                    Div("FastHTML", cls="badge badge-primary mr-2 mb-2"),
                    Div("Async Generators", cls="badge badge-secondary mr-2 mb-2"),
                    Div("Range Headers", cls="badge badge-accent mr-2 mb-2"),
                    Div("aiofiles", cls="badge badge-info mr-2 mb-2"),
                    Div("OpenCV", cls="badge badge-success mr-2 mb-2"),
                    Div("Thread Safety", cls="badge badge-warning mr-2 mb-2"),
                    cls="flex flex-wrap gap-2"
                ),
                cls="bg-gray-50 p-6 rounded-lg"
            ),
            
            cls="max-w-6xl mx-auto px-4 py-8"
        )
        
        return Layout(
            content,
            title="Streaming Demo | FastApp",
            current_path=f"{BASE}/demo",
            user=user,
            show_auth=True,
            demo=demo
        )
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "streaming_platform",
            "demo": demo,
            "camera_initialized": video_streaming_service.camera is not None
        }
    
    return app
