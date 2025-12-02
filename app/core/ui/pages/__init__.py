"""UI Pages Module"""
from .home import HomePage
from .about import AboutPage
from .contact import ContactPage
from .login import LoginPage
from .register import RegisterPage
from .profile import ProfilePage
from .admin import AdminDashboardPage
from .example_landing import ExamplePage
from .test import TestPage
from .docs import DocsPage

__all__ = [
    "HomePage",
    "AboutPage", 
    "ContactPage",
    "LoginPage",
    "RegisterPage",
    "ProfilePage",
    "AdminDashboardPage",
    "ExamplePage",
    "TestPage",
    "DocsPage"
]
