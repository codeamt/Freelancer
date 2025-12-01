"""Profile Page"""
from fasthtml.common import *
from monsterui.all import *

def ProfilePage(user):
    return Container(
        Div(
            Card(
                CardBody(
                    H1(f"Welcome, {user.get('sub', 'User')}", cls="mb-4"),
                    Div(
                        Strong("Role: "),
                        Span(user.get('role', 'user'), cls="text-muted"),
                        cls="mb-3"
                    ),
                    Div(
                        Strong("Email: "),
                        Span(user.get('sub', 'N/A'), cls="text-muted"),
                        cls="mb-3"
                    ),
                    Div(
                        Strong("Scopes: "),
                        Span(", ".join(user.get('scopes', [])), cls="text-muted"),
                        cls="mb-4"
                    ),
                    Button("Logout", 
                           hx_post="/auth/logout", 
                           hx_target="body", 
                           hx_swap="outerHTML",
                           cls="btn btn-danger")
                ),
                cls="shadow"
            ),
            cls="col-md-8 col-lg-6 mx-auto"
        ),
        cls="min-vh-100 d-flex align-items-center py-5"
    )
