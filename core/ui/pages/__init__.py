"""UI Pages Module"""
from .home import HomePage
from .about import AboutPage
from .contact import ContactPage
from .admin import AdminDashboardPage
from .admin_auth import WebAdminAuthPage, WebAdminDashboard
from .example_landing import ExamplePage
from .test import TestPage
from .docs import DocsPage
from .auth import AuthPage, AuthTabContent

__all__ = [
    "HomePage",
    "AboutPage", 
    "ContactPage",
    "AdminDashboardPage",
    "WebAdminAuthPage",
    "WebAdminDashboard",
    "ExamplePage",
    "TestPage",
    "DocsPage",
    "AuthPage",
    "AuthTabContent"
]
