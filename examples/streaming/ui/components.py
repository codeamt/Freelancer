"""Streaming UI components"""
from fasthtml.common import *
from monsterui.all import *


def VideoStreamCard(title: str, description: str, stream_url: str, snapshot_url: str, demo: bool = False):
    """Video stream card component"""
    return Card(
        Div(
            H3(title, cls="text-xl font-semibold mb-4"),
            P(description, cls="text-gray-600 mb-4"),
            Div(
                Img(src=stream_url, alt="Live Stream", 
                    cls="w-full rounded-lg shadow-lg mb-4"),
                cls="mb-4"
            ),
            Div(
                A("📸 Take Snapshot", href=snapshot_url, 
                  cls="btn btn-primary mr-2", target="_blank"),
                A("🔄 Refresh", href="#", cls="btn btn-outline", 
                  onclick="window.location.reload()"),
                cls="flex gap-2"
            ),
            cls="p-6"
        ),
        cls="hover:shadow-lg transition-shadow"
    )


def VideoUploadCard(title: str, description: str, upload_url: str, demo: bool = False):
    """Video upload card component"""
    return Card(
        Div(
            H3(title, cls="text-xl font-semibold mb-4"),
            P(description, cls="text-gray-600 mb-4"),
            Form(
                Input(type="file", accept="video/*", name="video", cls="mb-4"),
                Button("Upload & Stream", cls="btn btn-primary"),
                method="post",
                action=upload_url,
                enctype="multipart/form-data",
                cls="space-y-4"
            ),
            cls="p-6"
        ),
        cls="hover:shadow-lg transition-shadow"
    )


def StreamingHomePage(base_path: str, user: dict, live_streams: list, demo: bool = False):
    """Streaming platform home page component"""
    return Div(
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
                            A("Watch Now", href=f"{base_path}/watch/{stream.get('id')}", cls="btn btn-primary"),
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
                                Img(src=f"{base_path}/stream/video-stream", alt="Live Camera Stream", 
                                    cls="w-full max-w-2xl mx-auto rounded-lg shadow-lg"),
                                cls="flex justify-center mb-4"
                            ),
                            Div(
                                A("📸 Take Snapshot", href=f"{base_path}/stream/video-snapshot", 
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
                                action=f"{base_path}/stream/video-upload",
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


def StreamingLoginPage(base_path: str):
    """Streaming platform login page component"""
    return Div(
        Div(
            Div(
                H1("Login to Stream", cls="text-4xl font-bold mb-6 text-center"),
                P("Access your streaming dashboard and create amazing content", 
                  cls="text-lg text-gray-600 mb-8 text-center"),
                
                Form(
                    Input(
                        type="email", 
                        placeholder="Email address", 
                        name="email",
                        cls="w-full p-3 border rounded-lg mb-4"
                    ),
                    Input(
                        type="password", 
                        placeholder="Password", 
                        name="password",
                        cls="w-full p-3 border rounded-lg mb-6"
                    ),
                    Button("Login", cls="w-full btn btn-primary btn-lg"),
                    method="post",
                    action=f"{base_path}/auth/login",
                    cls="space-y-4"
                ),
                
                Div(
                    P("Don't have an account?", cls="text-center text-gray-600 mb-4"),
                    A("Sign up here", href=f"{base_path}/register", cls="btn btn-outline w-full"),
                    cls="text-center"
                ),
                
                cls="max-w-md mx-auto p-8 bg-white rounded-lg shadow-lg"
            ),
            cls="min-h-screen flex items-center justify-center bg-gray-50"
        )
    )
