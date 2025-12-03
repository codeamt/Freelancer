"""UI Pages Module"""
from .home import HomePage
from .about import AboutPage
from .contact import ContactPage
from .admin import AdminDashboardPage
from .example_landing import ExamplePage
from .test import TestPage
from .docs import DocsPage

# Note: LoginPage, RegisterPage, ProfilePage moved to add_ons/auth/ui/pages

__all__ = [
    "HomePage",
    "AboutPage", 
    "ContactPage",
    "AdminDashboardPage",
    "ExamplePage",
    "TestPage",
    "DocsPage"
]
