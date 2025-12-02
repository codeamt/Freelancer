"""
Social Network Example Application - Coming Soon

Placeholder for social networking features.
"""
from fasthtml.common import *
from monsterui.all import *
from core.ui.layout import Layout
from core.utils.logger import get_logger

logger = get_logger(__name__)


def create_social_app():
    """Create and configure the social network example app"""
    
    app = FastHTML(hdrs=[*Theme.slate.headers()])
    
    @app.get("/")
    def social_home():
        """Social network coming soon page"""
        
        content = Div(
            # Hero Section
            Div(
                Div(
                    # Icon
                    Div(
                        UkIcon("users", width="120", height="120", cls="text-blue-500 mb-8"),
                        cls="flex justify-center"
                    ),
                    
                    # Title
                    H1("🌐 Social Network", cls="text-5xl font-bold mb-4 text-center"),
                    P("Connect, Share, Engage", cls="text-2xl text-gray-500 mb-8 text-center"),
                    
                    # Coming Soon Badge
                    Div(
                        Span("🚧 Demo Coming Soon", cls="badge badge-lg badge-warning text-lg px-6 py-4"),
                        cls="flex justify-center mb-12"
                    ),
                    
                    # Features Preview
                    Div(
                        H2("Planned Features", cls="text-3xl font-bold mb-8 text-center"),
                        Div(
                            FeatureCard("👤", "User Profiles", "Customizable profiles with photos, bio, and interests"),
                            FeatureCard("📝", "Posts & Feed", "Share updates, photos, and videos with your network"),
                            FeatureCard("💬", "Messaging", "Real-time chat and direct messaging"),
                            FeatureCard("👥", "Connections", "Follow users and build your network"),
                            FeatureCard("❤️", "Interactions", "Like, comment, and share content"),
                            FeatureCard("🔔", "Notifications", "Stay updated with real-time notifications"),
                            FeatureCard("🔒", "Privacy Controls", "Manage who sees your content"),
                            FeatureCard("📊", "Analytics", "Track engagement and reach"),
                            FeatureCard("🎯", "Groups & Communities", "Create and join interest-based groups"),
                            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
                        ),
                    ),
                    
                    # Tech Stack
                    Div(
                        H3("Tech Stack", cls="text-2xl font-bold mb-6 text-center"),
                        Div(
                            TechBadge("FastHTML", "Web Framework"),
                            TechBadge("WebSockets", "Real-time Chat"),
                            TechBadge("MongoDB", "User Data & Posts"),
                            TechBadge("Redis", "Caching & Sessions"),
                            TechBadge("S3", "Media Storage"),
                            TechBadge("MonsterUI", "UI Components"),
                            cls="flex flex-wrap justify-center gap-3 mb-12"
                        ),
                    ),
                    
                    # CTA
                    Div(
                        A("← Back to Home", href="/", cls="btn btn-primary btn-lg mr-4"),
                        A("View Other Examples", href="#examples", cls="btn btn-outline btn-lg"),
                        cls="flex justify-center gap-4 mb-8"
                    ),
                    
                    # Example Sections
                    Div(
                        H3("Example Use Cases", cls="text-2xl font-bold mb-6 text-center", id="examples"),
                        Div(
                            UseCaseCard(
                                "Professional Network",
                                "LinkedIn-style platform for professionals",
                                ["Job postings", "Skills endorsements", "Company pages", "Professional messaging"]
                            ),
                            UseCaseCard(
                                "Community Platform",
                                "Facebook-style social network",
                                ["Personal profiles", "Photo albums", "Events", "Groups & pages"]
                            ),
                            UseCaseCard(
                                "Niche Social Network",
                                "Specialized community (e.g., artists, gamers, fitness)",
                                ["Interest-based feeds", "Portfolio sharing", "Challenges", "Leaderboards"]
                            ),
                            cls="grid grid-cols-1 md:grid-cols-3 gap-6"
                        ),
                    ),
                    
                    cls="max-w-6xl mx-auto"
                ),
                cls="py-16"
            )
        )
        
        return Layout(content, title="Social Network Example | FastApp")
    
    def FeatureCard(icon: str, title: str, description: str):
        """Feature card component"""
        return Card(
            Div(
                Div(icon, cls="text-4xl mb-3 text-center"),
                H3(title, cls="text-lg font-semibold mb-2 text-center"),
                P(description, cls="text-sm text-gray-500 text-center"),
                cls="p-6"
            ),
            cls="hover:shadow-lg transition-shadow"
        )
    
    def TechBadge(name: str, description: str):
        """Technology badge"""
        return Div(
            Span(name, cls="font-semibold"),
            Span(f" - {description}", cls="text-sm text-gray-500"),
            cls="badge badge-lg badge-outline"
        )
    
    def UseCaseCard(title: str, description: str, features: list):
        """Use case card"""
        return Card(
            Div(
                H4(title, cls="text-xl font-bold mb-3"),
                P(description, cls="text-gray-600 mb-4"),
                Ul(
                    *[Li(
                        UkIcon("check", width="16", height="16", cls="inline mr-2 text-green-500"),
                        feature,
                        cls="text-sm mb-2"
                    ) for feature in features],
                    cls="space-y-1"
                ),
                cls="p-6"
            ),
            cls="hover:shadow-lg transition-shadow"
        )
    
    return app
