"""Streaming UI components - Dark Mode"""
from fasthtml.common import *
from monsterui.all import *


def VideoStreamCard(title, description, stream_url, snapshot_url, demo=False):
    """Video stream card component - dark mode"""
    return Card(
        Div(
            H3(title, cls="text-xl font-semibold mb-2 text-white"),
            P(description, cls="text-gray-400 mb-4"),
            Img(src=stream_url, alt="Live Stream", cls="w-full rounded-lg mb-4"),
            Div(
                A("Take Snapshot", href=snapshot_url, cls="btn btn-primary mr-2", target="_blank"),
                A("Refresh", href="#", cls="btn btn-outline-secondary", onclick="window.location.reload()"),
                cls="flex gap-2"
            ),
            cls="p-6 bg-gray-800"
        ),
        cls="bg-gray-800 border-gray-700"
    )


def VideoUploadCard(title, description, upload_url, demo=False):
    """Video upload card component - dark mode"""
    return Card(
        Div(
            H3(title, cls="text-xl font-semibold mb-2 text-white"),
            P(description, cls="text-gray-400 mb-4"),
            Form(
                Input(type="file", accept="video/*", name="video", cls="mb-4 bg-gray-700 text-white border-gray-600"),
                Button("Upload & Stream", cls="btn btn-primary"),
                method="post",
                action=upload_url,
                enctype="multipart/form-data"
            ),
            cls="p-6 bg-gray-800"
        ),
        cls="bg-gray-800 border-gray-700"
    )


def StreamingHomePage(base_path, user, live_streams, demo=False):
    """Streaming platform home page - dark mode theme"""
    return Div(
        # Hero Section - Dark Mode
        Div(
            Div(
                Div(
                    UkIcon("play-circle", width="120", height="120", cls="text-red-400 mb-8"),
                    cls="flex justify-center"
                ),
                H1("📺 Streaming Platform", cls="text-5xl font-bold mb-4 text-center text-white"),
                P("Watch, Stream, Create", cls="text-2xl text-gray-300 mb-8 text-center"),
                Div(
                    Span("🔴 Live Demo Active", cls="badge badge-lg badge-success text-lg px-6 py-4 bg-green-600 text-white"),
                    cls="flex justify-center mb-12"
                ),
                cls="max-w-4xl mx-auto"
            ),
            cls="py-16 bg-gradient-to-br from-gray-900 via-gray-800 to-black"
        ),
        
        # Live Streams Section - Dark Mode
        Section(
            Div(
                H2("🎬 Live Streams", cls="text-3xl font-bold mb-8 text-center text-white"),
                Div(
                    *[Div(
                        H3(stream.get("title", "Untitled Stream"), cls="text-xl font-semibold mb-2 text-white"),
                        P(stream.get("description", "No description"), cls="text-gray-400 mb-4"),
                        Div(
                            Span(f"👁 {stream.get('viewer_count', 0)} viewers", cls="badge badge-primary mr-2 bg-blue-600 text-white"),
                            Span("🔴 LIVE", cls="badge badge-error bg-red-600 text-white"),
                            cls="flex gap-2 mb-4"
                        ),
                        A("Watch Now", href=f"{base_path}/watch/{stream.get('id')}", cls="btn btn-primary bg-red-600 hover:bg-red-700 text-white"),
                        cls="p-6 bg-gray-800 border border-gray-700 rounded-lg hover:shadow-lg transition-shadow"
                    ) for stream in live_streams[:6]],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
                ),
                cls="max-w-6xl mx-auto px-6"
            ),
            cls="py-16 bg-gray-800"
        ),
        
        # Demo Features - Dark Mode
        Section(
            Div(
                H2("🚀 Try Our Features", cls="text-3xl font-bold mb-8 text-center text-white"),
                Div(
                    # Camera Stream Demo
                    Div(
                        H3("📹 Live Camera Stream", cls="text-xl font-semibold mb-4 text-white"),
                        P("Real-time camera feed using async generators and OpenCV", cls="text-gray-400 mb-4"),
                        Div(
                            Img(src=f"{base_path}/stream/video-stream", alt="Live Camera Stream", 
                                cls="w-full max-w-2xl mx-auto rounded-lg shadow-lg mb-4 bg-gray-800 border border-gray-700"),
                            cls="flex justify-center mb-4"
                        ),
                        Div(
                            A("📸 Take Snapshot", href=f"{base_path}/stream/video-snapshot", 
                              cls="btn btn-primary bg-red-600 hover:bg-red-700 text-white mr-2", target="_blank"),
                            A("🔄 Refresh", href="#", cls="btn btn-outline bg-gray-700 hover:bg-gray-600 text-white border-gray-600", 
                              onclick="window.location.reload()"),
                            cls="flex justify-center gap-2"
                        ),
                        cls="mb-8 p-6 bg-gray-900 rounded-lg border border-gray-700"
                    ),
                    
                    # Video File Upload Demo
                    Div(
                        H3("🎬 Upload & Stream", cls="text-xl font-semibold mb-4 text-white"),
                        P("Upload video files and stream with range header support", cls="text-gray-400 mb-4"),
                        Form(
                            Input(type="file", accept="video/*", name="video", 
                                  cls="mb-4 bg-gray-700 text-white border-gray-600"),
                            Button("Upload & Stream", cls="btn btn-primary bg-blue-600 hover:bg-blue-700 text-white"),
                            method="post",
                            action=f"{base_path}/stream/video-upload",
                            enctype="multipart/form-data"
                        ),
                        cls="mb-8 p-6 bg-gray-900 rounded-lg border border-gray-700"
                    ),
                    
                    cls="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12"
                ),
                cls="max-w-6xl mx-auto px-6"
            ),
            cls="py-16 bg-gray-900"
        ),
        
        # Tech Stack - Dark Mode
        Section(
            Div(
                H3("🛠 Technology Stack", cls="text-2xl font-bold mb-6 text-center text-white"),
                Div(
                    Div("FastHTML", cls="badge badge-primary mr-2 mb-2 bg-blue-600 text-white"),
                    Div("Async Generators", cls="badge badge-secondary mr-2 mb-2 bg-purple-600 text-white"),
                    Div("Range Headers", cls="badge badge-accent mr-2 mb-2 bg-green-600 text-white"),
                    Div("aiofiles", cls="badge badge-info mr-2 mb-2 bg-cyan-600 text-white"),
                    Div("OpenCV", cls="badge badge-success mr-2 mb-2 bg-emerald-600 text-white"),
                    Div("Thread Safety", cls="badge badge-warning mr-2 mb-2 bg-amber-600 text-white"),
                    cls="flex flex-wrap justify-center"
                ),
                cls="max-w-6xl mx-auto px-6"
            ),
            cls="py-16 bg-black"
        )
    )


def StreamingLoginPage(base_path):
    """Streaming platform login page - dark mode"""
    return Div(
        Div(
            Div(
                H1("Login to Stream", cls="text-4xl font-bold mb-6 text-center text-white"),
                P("Access your streaming dashboard and create amazing content", 
                  cls="text-lg text-gray-400 mb-8 text-center"),
                
                Form(
                    Input(
                        type="email", 
                        placeholder="Email address", 
                        name="email",
                        cls="w-full p-3 border rounded-lg mb-4 bg-gray-700 text-white border-gray-600"
                    ),
                    Input(
                        type="password", 
                        placeholder="Password", 
                        name="password",
                        cls="w-full p-3 border rounded-lg mb-6 bg-gray-700 text-white border-gray-600"
                    ),
                    Button("Login", cls="w-full btn btn-primary btn-lg"),
                    method="post",
                    action=f"{base_path}/auth/login"
                ),
                
                Div(
                    P("Don't have an account?", cls="text-center text-gray-400 mb-4"),
                    A("Sign up here", href=f"{base_path}/register", cls="btn btn-outline-secondary w-full bg-gray-700 hover:bg-gray-600 text-white border-gray-600"),
                    cls="text-center"
                ),
                
                cls="max-w-md mx-auto p-8 bg-gray-800 rounded-lg shadow-lg border border-gray-700"
            ),
            cls="min-h-screen flex items-center justify-center bg-gray-900"
        )
    )
