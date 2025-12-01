"""Login Page"""
from fasthtml.common import *
from monsterui.all import *

def LoginPage():
    return Container(
        Div(
            Card(
                CardBody(
                    H1("Login to FastApp", cls="text-center mb-4"),
                    Form(
                        Div(
                            Label("Email", fr="email", cls="form-label"),
                            Input(type="email", id="email", name="email", placeholder="your@email.com", 
                                  cls="form-control", required=True),
                            cls="mb-3"
                        ),
                        Div(
                            Label("Password", fr="password", cls="form-label"),
                            Input(type="password", id="password", name="password", placeholder="••••••••", 
                                  cls="form-control", required=True),
                            cls="mb-3"
                        ),
                        Button("Login", type="submit", cls="btn btn-primary w-100 mb-3"),
                        Div(
                            P(A("Don't have an account? Register here", href="/auth/register", cls="text-decoration-none"), 
                              cls="text-center mb-0"),
                        ),
                        hx_post="/auth/login",
                        hx_target="#login-result"
                    ),
                    Hr(cls="my-4"),
                    Div(
                        P("Or continue with", cls="text-center text-muted mb-3"),
                        A(
                            Button("Sign in with Google", cls="btn btn-outline-secondary w-100"),
                            href="/auth/google/login"
                        ),
                    ),
                    Div(id="login-result", cls="mt-3")
                ),
                cls="shadow"
            ),
            cls="col-md-6 col-lg-4 mx-auto"
        ),
        cls="min-vh-100 d-flex align-items-center py-5"
    )
