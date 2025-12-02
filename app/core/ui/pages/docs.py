"""Documentation Page"""
from fasthtml.common import *
from monsterui.all import *

def DocsPage():
    return Div(
        # Header
        Div(
            H1("Documentation", cls="text-4xl font-bold mb-4"),
            P("Learn how to build powerful web applications with FastApp", cls="text-xl text-gray-400 mb-8"),
            cls="mb-12"
        ),
        
        # Quick Start
        Div(
            H2("Quick Start", cls="text-3xl font-bold mb-4"),
            Card(
                Div(
                    H3("Installation", cls="text-xl font-semibold mb-3"),
                    Pre(
                        Code(
                            "git clone https://github.com/yourusername/fastapp.git\n"
                            "cd fastapp\n"
                            "uv venv\n"
                            "source .venv/bin/activate\n"
                            "uv pip install -r requirements.txt\n"
                            "uv run python app/app.py",
                            cls="text-sm"
                        ),
                        cls="bg-base-200 p-4 rounded-lg overflow-x-auto"
                    ),
                    cls="p-6"
                ),
                cls="mb-8"
            ),
            cls="mb-12"
        ),
        
        # Core Concepts
        Div(
            H2("Core Concepts", cls="text-3xl font-bold mb-6"),
            Div(
                # FastHTML
                Card(
                    Div(
                        Div(
                            UkIcon("zap", cls="text-4xl text-primary mb-3"),
                            cls="flex justify-center"
                        ),
                        H3("FastHTML", cls="text-xl font-semibold mb-2 text-center"),
                        P("Modern Python web framework for building reactive applications with minimal JavaScript.", 
                          cls="text-gray-400 text-center"),
                        cls="p-6"
                    ),
                    cls="mb-4"
                ),
                # MonsterUI
                Card(
                    Div(
                        Div(
                            UkIcon("palette", cls="text-4xl text-secondary mb-3"),
                            cls="flex justify-center"
                        ),
                        H3("MonsterUI", cls="text-xl font-semibold mb-2 text-center"),
                        P("Beautiful UI components built on Tailwind CSS and DaisyUI for rapid development.", 
                          cls="text-gray-400 text-center"),
                        cls="p-6"
                    ),
                    cls="mb-4"
                ),
                # Add-ons
                Card(
                    Div(
                        Div(
                            UkIcon("grid", cls="text-4xl text-accent mb-3"),
                            cls="flex justify-center"
                        ),
                        H3("Modular Add-ons", cls="text-xl font-semibold mb-2 text-center"),
                        P("Plug-and-play modules for LMS, e-commerce, and social features.", 
                          cls="text-gray-400 text-center"),
                        cls="p-6"
                    ),
                    cls="mb-4"
                ),
                cls="grid grid-cols-1 md:grid-cols-3 gap-6"
            ),
            cls="mb-12"
        ),
        
        # Add-ons Documentation
        Div(
            H2("Available Add-ons", cls="text-3xl font-bold mb-6"),
            
            # LMS
            Card(
                Div(
                    H3(UkIcon("book", cls="inline mr-2"), "LMS - Learning Management System", cls="text-2xl font-semibold mb-3"),
                    P("Build complete e-learning platforms with course management, student tracking, and certification.", cls="mb-4 text-gray-400"),
                    Ul(
                        Li("Course creation and management"),
                        Li("Student enrollment and progress tracking"),
                        Li("Quiz and assessment tools"),
                        Li("Certificate generation"),
                        Li("Discussion forums"),
                        cls="list-disc list-inside space-y-2 text-gray-400"
                    ),
                    cls="p-6"
                ),
                cls="mb-6"
            ),
            
            # Commerce
            Card(
                Div(
                    H3(UkIcon("shopping-cart", cls="inline mr-2"), "Commerce - Online Store", cls="text-2xl font-semibold mb-3"),
                    P("Full-featured e-commerce solution with payment processing and inventory management.", cls="mb-4 text-gray-400"),
                    Ul(
                        Li("Product catalog management"),
                        Li("Shopping cart and checkout"),
                        Li("Payment gateway integration"),
                        Li("Order management"),
                        Li("Inventory tracking"),
                        cls="list-disc list-inside space-y-2 text-gray-400"
                    ),
                    cls="p-6"
                ),
                cls="mb-6"
            ),
            
            # Social
            Card(
                Div(
                    H3(UkIcon("users", cls="inline mr-2"), "Social - Community Platform", cls="text-2xl font-semibold mb-3"),
                    P("Build engaged communities with user profiles, posts, and real-time messaging.", cls="mb-4 text-gray-400"),
                    Ul(
                        Li("User profiles and authentication"),
                        Li("Posts, comments, and likes"),
                        Li("Real-time messaging"),
                        Li("Activity feeds"),
                        Li("Notifications"),
                        cls="list-disc list-inside space-y-2 text-gray-400"
                    ),
                    cls="p-6"
                ),
                cls="mb-6"
            ),
            cls="mb-12"
        ),
        
        # API Reference
        Div(
            H2("API Reference", cls="text-3xl font-bold mb-6"),
            P("Detailed API documentation coming soon. Check the ", 
              A("GitHub repository", href="https://github.com/yourusername/fastapp", cls="text-primary hover:underline"),
              " for code examples.",
              cls="text-gray-400"),
            cls="mb-12"
        ),
        
        cls="max-w-6xl mx-auto"
    )
